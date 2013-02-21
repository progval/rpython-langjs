from rpython.rlib.rarithmetic import ovfcheck_float_to_int
from rpython.rlib.parsing.tree import RPythonVisitor, Symbol
from rpython.rlib.objectmodel import enforceargs

from js import operations

from js.symbol_map import SymbolMap


class FakeParseError(Exception):
    def __init__(self, pos, msg):
        self.pos = pos
        self.msg = msg


class ASTBuilder(RPythonVisitor):
    BINOP_TO_CLS = {
        '+': operations.Plus,
        '-': operations.Sub,
        '*': operations.Mult,
        '/': operations.Division,
        '%': operations.Mod,
        '^': operations.BitwiseXor,
        '|': operations.BitwiseOr,
        '&': operations.BitwiseAnd,
        '&&': operations.And,
        '||': operations.Or,
        '==': operations.Eq,
        '!=': operations.Ne,
        '!==': operations.StrictNe,
        '===': operations.StrictEq,
        '>': operations.Gt,
        '>=': operations.Ge,
        '<': operations.Lt,
        '<=': operations.Le,
        '>>': operations.Rsh,
        '>>>': operations.Ursh,
        '<<': operations.Lsh,
        '.': operations.MemberDot,
        '[': operations.Member,
        ',': operations.Comma,
        'in': operations.In,
        'instanceof': operations.InstanceOf,
    }
    UNOP_TO_CLS = {
        '~': operations.BitwiseNot,
        '!': operations.Not,
        '+': operations.UPlus,
        '-': operations.UMinus,
        'typeof': operations.Typeof,
        'void': operations.Void,
        'delete': operations.Delete,
    }
    LISTOP_TO_CLS = {
        '[': operations.Array,
        '{': operations.ObjectInit,
    }

    def __init__(self):
        self.funclists = []
        self.scopes = []
        self.sourcename = ""
        self.depth = -1

    def enter_scope(self):
        self.depth = self.depth + 1

        new_scope = SymbolMap()
        self.scopes.append(new_scope)
        #print 'starting new scope %d' % (self.depth, )

    def declare_symbol(self, symbol):
        s = unicode(symbol)
        #assert isinstance(s, unicode)
        idx = self.scopes[-1].add_symbol(s)
        #print 'symbol "%s"@%d in scope %d' % (symbol, idx, self.depth,)
        return idx

    def declare_variable(self, symbol):
        s = unicode(symbol)
        #assert isinstance(s, unicode)
        idx = self.scopes[-1].add_variable(s)
        #print 'var declaration "%s"@%d in scope %d' % (symbol, idx, self.depth,)
        return idx

    def declare_function(self, symbol, funcobj):
        s = unicode(symbol)
        #assert isinstance(s, unicode)
        self.funclists[-1][s] = funcobj
        idx = self.scopes[-1].add_function(s)
        #print 'func declaration "%s"@%d in scope %d' % (symbol, idx, self.depth,)
        return idx

    def declare_parameter(self, symbol):
        idx = self.scopes[-1].add_parameter(symbol)
        #print 'parameter declaration "%s"@%d in scope %d' % (symbol, idx, self.depth,)
        return idx

    def exit_scope(self):
        self.depth = self.depth - 1
        self.scopes.pop()
        #print 'closing scope, returning to %d' % (self.depth, )

    def current_scope_variables(self):
        return self.current_scope().variables

    def current_scope_parameters(self):
        return self.current_scope().parameters

    def current_scope(self):
        try:
            return self.scopes[-1]
        except IndexError:
            return None

    def set_sourcename(self, sourcename):
        self.stsourcename = sourcename  # XXX I should call this

    def get_pos(self, node):
        value = ''
        source_pos = None
        if isinstance(node, Symbol):
            value = node.additional_info
            source_pos = node.token.source_pos
        elif len(node.children) > 0:
            curr = node.children[0]
            while not isinstance(curr, Symbol):
                if len(curr.children):
                    curr = curr.children[0]
                else:
                    break
            else:
                value = curr.additional_info
                source_pos = curr.token.source_pos

        # XXX some of the source positions are not perfect
        if source_pos is None:
            return operations.Position()
        return operations.Position(
            source_pos.lineno,
            source_pos.columnno,
            source_pos.columnno + len(value))

    def visit_DECIMALLITERAL(self, node):
        pos = self.get_pos(node)
        try:

            f = float(node.additional_info)
            i = ovfcheck_float_to_int(f)
            if i != f:
                return operations.FloatNumber(pos, f)
            else:
                return operations.IntNumber(pos, i)
        except (ValueError, OverflowError):
            return operations.FloatNumber(pos, float(node.additional_info))

    def visit_HEXINTEGERLITERAL(self, node):
        pos = self.get_pos(node)
        hexlit = node.additional_info
        if hexlit.startswith('0x') or hexlit.startswith('0X'):
            hexlit = hexlit[2:]
        return operations.IntNumber(pos, int(hexlit, 16))

    def visit_OCTALLITERAL(self, node):
        pos = self.get_pos(node)
        return operations.IntNumber(pos, int(node.additional_info, 8))

    def string(self, node):
        from js.operations import string_unquote
        from js.runistr import unicode_unescape, decode_str_utf8

        # TODO decode utf-8
        pos = self.get_pos(node)
        s = node.additional_info
        strval = decode_str_utf8(s)
        strval = string_unquote(strval)
        strval = unicode_unescape(strval)

        return operations.String(pos, strval)
    visit_DOUBLESTRING = string
    visit_SINGLESTRING = string

    def binaryop(self, node):
        left = self.dispatch(node.children[0])
        for i in range((len(node.children) - 1) // 2):
            op = node.children[i * 2 + 1]
            pos = self.get_pos(op)
            right = self.dispatch(node.children[i * 2 + 2])
            result = self.BINOP_TO_CLS[op.additional_info](pos, left, right)
            left = result
        return left
    visit_additiveexpression = binaryop
    visit_multiplicativeexpression = binaryop
    visit_bitwisexorexpression = binaryop
    visit_bitwiseandexpression = binaryop
    visit_bitwiseorexpression = binaryop
    visit_equalityexpression = binaryop
    visit_logicalorexpression = binaryop
    visit_logicalandexpression = binaryop
    visit_relationalexpression = binaryop
    visit_shiftexpression = binaryop
    visit_expression = binaryop
    visit_expressionnoin = binaryop

    def visit_memberexpression(self, node):
        if isinstance(node.children[0], Symbol) and \
                node.children[0].additional_info == 'new':  # XXX could be a identifier?
            pos = self.get_pos(node)
            left = self.dispatch(node.children[1])
            right = self.dispatch(node.children[2])
            return operations.NewWithArgs(pos, left, right)
        else:
            return self.binaryop(node)

    def literalop(self, node):
        pos = self.get_pos(node)
        value = node.children[0].additional_info
        if value == "true":
            return operations.Boolean(pos, True)
        elif value == "false":
            return operations.Boolean(pos, False)
        else:
            return operations.Null(pos)
    visit_nullliteral = literalop
    visit_booleanliteral = literalop

    def visit_unaryexpression(self, node):
        op = node.children[0]
        pos = self.get_pos(op)
        child = self.dispatch(node.children[1])
        if op.additional_info in ['++', '--']:
            return self._dispatch_assignment(pos, child, op.additional_info,
                                             'pre')
        return self.UNOP_TO_CLS[op.additional_info](pos, child)

    def _dispatch_assignment(self, pos, left, atype, prepost):
        is_post = prepost == 'post'
        if self.is_local_identifier(left):
            return operations.LocalAssignmentOperation(pos, left, None, atype, is_post)
        elif self.is_identifier(left):
            return operations.AssignmentOperation(pos, left, left.name, left.index, None, atype, is_post)
        elif self.is_member(left):
            return operations.MemberAssignmentOperation(pos, left, None, atype, is_post)
        else:
            raise FakeParseError(pos, "invalid lefthand expression")

    def visit_postfixexpression(self, node):
        op = node.children[1]
        pos = self.get_pos(op)
        child = self.dispatch(node.children[0])
        # all postfix expressions are assignments
        return self._dispatch_assignment(pos, child, op.additional_info, 'post')

    def listop(self, node):
        op = node.children[0]
        pos = self.get_pos(op)
        l = [self.dispatch(child) for child in node.children[1:]]
        return self.LISTOP_TO_CLS[op.additional_info](pos, l)
    visit_arrayliteral = listop  # elision
    visit_objectliteral = listop

    def visit_block(self, node):
        op = node.children[0]
        pos = self.get_pos(op)
        l = [self.dispatch(child) for child in node.children[1:]]

        nodes = []
        for node in l:
            if not(node is None or isinstance(node, operations.Empty)):
                nodes.append(node)

        return operations.Block(pos, nodes)

    def visit_arguments(self, node):
        pos = self.get_pos(node)
        nodes = [self.dispatch(child) for child in node.children[1:]]
        return operations.ArgumentList(pos, nodes)

    def visit_formalparameterlist(self, node):
        pos = self.get_pos(node)
        nodes = [self.dispatch(child) for child in node.children]
        for node in nodes:
            self.declare_parameter(node.name)
        return operations.ArgumentList(pos, nodes)

    def visit_variabledeclarationlist(self, node):
        pos = self.get_pos(node)
        nodes = [self.dispatch(child) for child in node.children]
        return operations.VariableDeclList(pos, nodes)
    visit_variabledeclarationlistnoin = visit_variabledeclarationlist

    def visit_propertynameandvalue(self, node):
        pos = self.get_pos(node)
        l = node.children[0]
        if l.symbol == "IDENTIFIERNAME":
            identifier = l.additional_info
            i = unicode(identifier)
            #assert isinstance(i, unicode)
            index = self.declare_symbol(i)
            lpos = self.get_pos(l)
            left = operations.Identifier(lpos, i, index)
        else:
            left = self.dispatch(l)
        right = self.dispatch(node.children[1])
        return operations.PropertyInit(pos, left, right)

    def visit_IDENTIFIERNAME(self, node):
        pos = self.get_pos(node)
        name = node.additional_info
        n = unicode(name)
        #assert isinstance(n, unicode)
        index = self.declare_symbol(n)
        #if self.scopes.is_local(name):
            #local = self.scopes.get_local(name)
            #return operations.LocalIdentifier(pos, name, local)
        return operations.Identifier(pos, n, index)

    def visit_program(self, node):
        self.enter_scope()
        pos = self.get_pos(node)
        body = self.dispatch(node.children[0])
        scope = self.current_scope()
        final_scope = scope.finalize()
        return operations.Program(pos, body, final_scope)

    def visit_variablestatement(self, node):
        pos = self.get_pos(node)
        body = self.dispatch(node.children[0])
        return operations.Variable(pos, body)

    def visit_throwstatement(self, node):
        pos = self.get_pos(node)
        exp = self.dispatch(node.children[0])
        return operations.Throw(pos, exp)

    def visit_sourceelements(self, node):
        pos = self.get_pos(node)
        self.funclists.append({})
        nodes = []

        for child in node.children:
            n = self.dispatch(child)
            if not (n is None or isinstance(n, operations.Empty)):
                nodes.append(n)

        var_decl = self.current_scope_variables()
        func_decl = self.funclists.pop()

        return operations.SourceElements(pos, var_decl, func_decl, nodes, self.sourcename)

    def functioncommon(self, node, declaration=True):
        self.enter_scope()

        pos = self.get_pos(node)
        i = 0
        identifier, i = self.get_next_expr(node, i)
        parameters, i = self.get_next_expr(node, i)
        functionbody, i = self.get_next_expr(node, i)

        if identifier is not None:
            funcname = identifier.get_literal()
        else:
            funcname = u''

        scope = self.current_scope()
        final_scope = scope.finalize()

        self.exit_scope()

        funcindex = -1
        if declaration:
            f = unicode(funcname)
            #assert isinstance(f, unicode)
            funcindex = self.declare_symbol(f)

        funcobj = operations.FunctionStatement(pos, funcname, funcindex, functionbody, final_scope)

        if declaration:
            self.declare_function(funcname, funcobj)

        return funcobj

    def visit_functiondeclaration(self, node):
        self.functioncommon(node)
        return None

    def visit_functionexpression(self, node):
        return self.functioncommon(node, declaration=False)

    def visit_variabledeclaration(self, node):
        pos = self.get_pos(node)
        identifier = self.dispatch(node.children[0])
        identifier_name = identifier.get_literal()
        index = self.declare_variable(identifier_name)
        if len(node.children) > 1:
            expr = self.dispatch(node.children[1])
        else:
            expr = None

        #if self.scopes.is_local(identifier_name):
        #    local = self.scopes.get_local(identifier_name)
        #    return operations.LocalVariableDeclaration(pos, identifier, local, expr)
        #else:
        return operations.VariableDeclaration(pos, identifier, index, expr)
    visit_variabledeclarationnoin = visit_variabledeclaration

    def visit_expressionstatement(self, node):
        pos = self.get_pos(node)
        return operations.ExprStatement(pos, self.dispatch(node.children[0]))

    def visit_callexpression(self, node):
        pos = self.get_pos(node)
        left = self.dispatch(node.children[0])
        nodelist = node.children[1:]
        while nodelist:
            currnode = nodelist.pop(0)
            if isinstance(currnode, Symbol):
                op = currnode
                right = self.dispatch(nodelist.pop(0))
                left = self.BINOP_TO_CLS[op.additional_info](pos, left, right)
            else:
                right = self.dispatch(currnode)
                left = operations.Call(pos, left, right)

        return left

    def is_identifier(self, obj):
        from js.operations import Identifier
        return isinstance(obj, Identifier)

    def is_member(self, obj):
        from js.operations import Member, MemberDot
        return isinstance(obj, Member) or isinstance(obj, MemberDot)

    def is_local_identifier(self, obj):
        #from js.operations import LocalIdentifier
        #return isinstance(obj, LocalIdentifier)
        return False

    def visit_assignmentexpression(self, node):

        pos = self.get_pos(node)
        left = self.dispatch(node.children[0])
        operation = node.children[1].additional_info
        right = self.dispatch(node.children[2])

        if self.is_local_identifier(left):
            return operations.LocalAssignmentOperation(pos, left, right, operation)
        elif self.is_identifier(left):
            identifier = left.get_literal()
            i = unicode(identifier)
            #assert isinstance(i, unicode)
            index = self.declare_symbol(i)
            return operations.AssignmentOperation(pos, left, identifier, index, right, operation)
        elif self.is_member(left):
            return operations.MemberAssignmentOperation(pos, left, right, operation)
        else:
            raise FakeParseError(pos, "invalid lefthand expression")
    visit_assignmentexpressionnoin = visit_assignmentexpression

    def visit_emptystatement(self, node):
        pos = self.get_pos(node)
        return operations.Empty(pos)

    def visit_newexpression(self, node):
        if len(node.children) == 1:
            return self.dispatch(node.children[0])
        else:
            pos = self.get_pos(node)
            val = self.dispatch(node.children[1])
            return operations.New(pos, val)

    def visit_ifstatement(self, node):
        pos = self.get_pos(node)
        condition = self.dispatch(node.children[0])
        ifblock = self.dispatch(node.children[1])
        if len(node.children) > 2:
            elseblock = self.dispatch(node.children[2])
        else:
            elseblock = None
        return operations.If(pos, condition, ifblock, elseblock)

    def visit_iterationstatement(self, node):
        return self.dispatch(node.children[0])

    def visit_switchstatement(self, node):
        pos = self.get_pos(node)
        expression = self.dispatch(node.children[0])
        caseblock = self.dispatch(node.children[1])
        return operations.Switch(pos, expression, caseblock.clauses, caseblock.default_clause)

    def visit_caseblock(self, node):
        pos = self.get_pos(node)
        caseclauses = self.dispatch(node.children[0]).clauses
        if len(node.children) > 1:
            defaultblock = self.dispatch(node.children[1])
        else:
            defaultblock = operations.EmptyExpression(pos)
        return operations.CaseBlock(pos, caseclauses, defaultblock)

    def visit_caseclauses(self, node):
        pos = self.get_pos(node)
        expressions = []
        clauses = []
        for c in node.children:
            if c.symbol == 'statementlist':
                block = self.dispatch(c)
                clauses.append(operations.CaseClause(pos, expressions, block))
                expressions = []
            else:
                expressions.append(self.dispatch(c))
        return operations.CaseClauses(pos, clauses)

    def visit_defaultclause(self, node):
        pos = self.get_pos(node)
        block = self.dispatch(node.children[0])
        return operations.DefaultClause(pos, block)

    def visit_statementlist(self, node):
        pos = self.get_pos(node)
        block = self.dispatch(node.children[0])
        return operations.StatementList(pos, block)

    def visit_whiles(self, node):
        pos = self.get_pos(node)
        itertype = node.children[0].additional_info
        if itertype == 'while':
            condition = self.dispatch(node.children[1])
            block = self.dispatch(node.children[2])
            return operations.While(pos, condition, block)
        elif itertype == "do":
            condition = self.dispatch(node.children[2])
            block = self.dispatch(node.children[1])
            return operations.Do(pos, condition, block)
        else:
            raise NotImplementedError("Unknown while version %s" % (itertype,))

    def visit_regularfor(self, node):
        pos = self.get_pos(node)
        i = 1
        setup, i = self.get_next_expr(node, i)
        condition, i = self.get_next_expr(node, i)
        if isinstance(condition, operations.Undefined):
            condition = operations.Boolean(pos, True)
        update, i = self.get_next_expr(node, i)
        body, i = self.get_next_expr(node, i)

        if setup is None:
            setup = operations.EmptyExpression(pos)
        if condition is None:
            condition = operations.Boolean(pos, True)
        if update is None:
            update = operations.EmptyExpression(pos)
        if body is None:
            body = operations.EmptyExpression(pos)

        return operations.For(pos, setup, condition, update, body)
    visit_regularvarfor = visit_regularfor

    def visit_infor(self, node):
        pos = self.get_pos(node)
        left = self.dispatch(node.children[1])
        right = self.dispatch(node.children[2])
        body = self.dispatch(node.children[3])
        return operations.ForIn(pos, left, right, body)

    def visit_invarfor(self, node):
        pos = self.get_pos(node)
        left = self.dispatch(node.children[1])
        right = self.dispatch(node.children[2])
        body = self.dispatch(node.children[3])
        return operations.ForIn(pos, left, right, body)

    def get_next_expr(self, node, i):
        if isinstance(node.children[i], Symbol) and node.children[i].additional_info in [';', ')', '(', '}']:
            return None, i + 1
        else:
            return self.dispatch(node.children[i]), i + 2

    def visit_breakstatement(self, node):
        pos = self.get_pos(node)
        if len(node.children) > 0:
            target = self.dispatch(node.children[0])
        else:
            target = None
        return operations.Break(pos, target)

    def visit_continuestatement(self, node):
        pos = self.get_pos(node)
        if len(node.children) > 0:
            target = self.dispatch(node.children[0])
        else:
            target = None
        return operations.Continue(pos, target)

    def visit_returnstatement(self, node):
        pos = self.get_pos(node)
        if len(node.children) > 0:
            value = self.dispatch(node.children[0])
        else:
            value = None
        return operations.Return(pos, value)

    def visit_conditionalexpression(self, node):
        pos = self.get_pos(node)
        condition = self.dispatch(node.children[0])
        truepart = self.dispatch(node.children[2])
        falsepart = self.dispatch(node.children[3])
        return operations.If(pos, condition, truepart, falsepart)

    def visit_trystatement(self, node):
        pos = self.get_pos(node)
        tryblock = self.dispatch(node.children[0])
        catchparam = None
        catchblock = None
        finallyblock = None
        if node.children[1].children[0].additional_info == "catch":
            catchparam = self.dispatch(node.children[1].children[1])
            catchblock = self.dispatch(node.children[1].children[2])
            if len(node.children) > 2:
                finallyblock = self.dispatch(node.children[2].children[1])
        else:
            finallyblock = self.dispatch(node.children[1].children[1])
        return operations.Try(pos, tryblock, catchparam, catchblock, finallyblock)

    def visit_primaryexpression(self, node):
        pos = self.get_pos(node)
        return operations.This(pos)

    def visit_withstatement(self, node):
        pos = self.get_pos(node)
        identifier = self.dispatch(node.children[0])
        body = self.dispatch(node.children[1])
        return operations.With(pos, identifier, body)

ASTBUILDER = ASTBuilder()


# XXX this is somewhat hackish
def new_ast_builder():
    b = ASTBuilder()  # ASTBUILDER
    #b.funclists = []
    #b.scopes = Scopes()
    #b.sourcename = ""
    return b


def make_ast_builder(sourcename=''):
    b = new_ast_builder()  # ASTBuilder()
    b.set_sourcename(sourcename)
    return b


def parse_tree_to_ast(parse_tree):
    builder = make_ast_builder()
    tree = builder.dispatch(parse_tree)
    return tree


@enforceargs(unicode)
def parse_to_ast(code):
    #assert isinstance(code, unicode)
    from js.jsparser import parse
    from js.runistr import encode_unicode_utf8
    src = encode_unicode_utf8(code)
    parse_tree = parse(src)
    ast = parse_tree_to_ast(parse_tree)
    return ast
