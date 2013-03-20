# encoding: utf-8
"""
operations.py
Implements the javascript operations nodes for the interpretation tree
"""
from rpython.rlib.unroll import unrolling_iterable
from rpython.rlib.objectmodel import enforceargs

from js.exception import JsTypeError, JsException


class Position(object):
    def __init__(self, lineno=-1, start=-1, end=-1):
        self.lineno = lineno
        self.start = start
        self.end = end

    def __repr__(self):
        return "l:%d %d,%d" % (self.lineno, self.start, self.end)


class Node(object):
    """
    Node is the base class for all the other nodes.
    """
    def __init__(self, pos):
        """
        Initializes the content from the AST specific for each node type
        """
        raise NotImplementedError()

    def emit(self, bytecode):
        """ Emits bytecode
        """
        raise NotImplementedError()

    def get_literal(self):
        raise NotImplementedError()

    def get_args(self, ctx):
        raise NotImplementedError()

    def __str__(self):
        return "%s()" % (self.__class__)


class Statement(Node):
    def __init__(self, pos):
        self.pos = pos


class ExprStatement(Node):
    def __init__(self, pos, expr):
        self.pos = pos
        self.expr = expr

    def emit(self, bytecode):
        self.expr.emit(bytecode)


class Expression(Statement):
    pass


class ListOp(Expression):
    def __init__(self, pos, nodes):
        self.pos = pos
        self.nodes = nodes


def create_unary_op(name):
    class UnaryOp(Expression):
        def __init__(self, pos, expr, postfix=False):
            self.pos = pos
            self.expr = expr
            self.postfix = postfix

        def emit(self, bytecode):
            self.expr.emit(bytecode)
            bytecode.emit(name)
    UnaryOp.__name__ = name
    return UnaryOp


def create_binary_op(name):
    class BinaryOp(Expression):
        def __init__(self, pos, left, right):
            self.pos = pos
            self.left = left
            self.right = right

        def emit(self, bytecode):
            self.left.emit(bytecode)
            self.right.emit(bytecode)
            bytecode.emit(name)
    BinaryOp.__name__ = name
    return BinaryOp


class Undefined(Statement):
    def emit(self, bytecode):
        bytecode.emit('LOAD_UNDEFINED')


class PropertyInit(Expression):
    def __init__(self, pos, lefthand, expr):
        self.pos = pos
        self.lefthand = lefthand
        self.expr = expr

    def emit(self, bytecode):
        self.expr.emit(bytecode)
        if isinstance(self.lefthand, Identifier):
            bytecode.emit('LOAD_STRINGCONSTANT', self.lefthand.name)
        else:
            self.lefthand.emit(bytecode)


class Array(ListOp):
    def emit(self, bytecode):
        for element in self.nodes:
            element.emit(bytecode)
        bytecode.emit('LOAD_ARRAY', len(self.nodes))


OPERANDS = {
    '+=': 'ADD',
    '-=': 'SUB',
    '*=': 'MUL',
    '/=': 'DIV',
    '++': 'INCR',
    '--': 'DECR',
    '%=': 'MOD',
    '&=': 'BITAND',
    '|=': 'BITOR',
    '^=': 'BITXOR',
    '>>=': 'RSH',
    '<<=': 'LSH',
    '>>>=': 'URSH'
}

OPERATIONS = unrolling_iterable(OPERANDS.items())


class BaseAssignment(Expression):
    noops = ['=']

    def has_operation(self):
        return self.operand not in self.noops

    def post_operation(self):
        return self.post

    def emit(self, bytecode):
        if self.has_operation():
            self.left.emit(bytecode)
            if self.post_operation():
                # Force ToNumber
                bytecode.emit('UPLUS')
                bytecode.emit('DUP')
            self.right.emit(bytecode)
            self.emit_operation(bytecode)
        else:
            self.right.emit(bytecode)

        self.emit_store(bytecode)

        if self.post_operation():
            bytecode.emit('POP')

    def emit_operation(self, bytecode):
        # calls to bytecode.emit have to be very very very static
        op = self.operand
        for key, value in OPERATIONS:
            if op == key:
                bytecode.emit(value)
                return
        assert 0

    def emit_store(self, bytecode):
        raise NotImplementedError


class AssignmentOperation(BaseAssignment):
    def __init__(self, pos, left, identifier, index, right, operand, post=False):
        self.left = left
        self.identifier = identifier
        self.index = index
        self.right = right
        if self.right is None:
            self.right = Empty(pos)
        self.pos = pos
        self.operand = operand
        self.post = post

    def emit_store(self, bytecode):
        bytecode.emit('STORE', self.index, self.identifier)


class LocalAssignmentOperation(AssignmentOperation):
    def __init__(self, pos, left, right, operand, post=False):
        self.left = left
        self.local = left.get_local()
        self.identifier = left.get_literal()
        self.right = right
        if self.right is None:
            self.right = Empty(pos)
        self.pos = pos
        self.operand = operand
        self.post = post

    def emit_store(self, bytecode):
        bytecode.emit('STORE_LOCAL', self.local)


class MemberAssignmentOperation(BaseAssignment):
    def __init__(self, pos, left, right, operand, post=False):
        self.pos = pos
        self.left = left
        self.right = right
        if right is None:
            self.right = Empty(pos)

        self.operand = operand

        self.w_object = self.left.left
        self.expr = self.left.expr
        self.post = post

    def emit_store(self, bytecode):
        self.expr.emit(bytecode)
        self.w_object.emit(bytecode)
        bytecode.emit('STORE_MEMBER')


class Block(Statement):
    def __init__(self, pos, nodes):
        self.pos = pos
        self.nodes = nodes

    def emit(self, bytecode):
        if len(self.nodes) > 1:
            for node in self.nodes[:-1]:
                node.emit(bytecode)
                bytecode.emit('POP')
        if len(self.nodes) > 0:
            node = self.nodes[-1]
            node.emit(bytecode)
        else:
            bytecode.emit('LOAD_UNDEFINED')

BitwiseAnd = create_binary_op('BITAND')
BitwiseXor = create_binary_op('BITXOR')
BitwiseOr = create_binary_op('BITOR')

BitwiseNot = create_unary_op('BITNOT')


class Unconditional(Statement):
    def __init__(self, pos, target):
        self.pos = pos
        self.target = target


class Break(Unconditional):
    def emit(self, bytecode):
        assert self.target is None
        bytecode.emit('LOAD_UNDEFINED')
        bytecode.emit_break()


class Continue(Unconditional):
    def emit(self, bytecode):
        assert self.target is None
        bytecode.emit('LOAD_UNDEFINED')
        bytecode.emit_continue()


class Call(Expression):
    def __init__(self, pos, left, args):
        self.pos = pos
        self.left = left
        self.args = args

    def emit(self, bytecode):
        self.args.emit(bytecode)
        left = self.left
        if isinstance(left, MemberDot):
            left.left.emit(bytecode)
            # XXX optimise
            bytecode.emit('LOAD_STRINGCONSTANT', left.name)
            bytecode.emit('CALL_METHOD')
        elif isinstance(left, Member):
            raise NotImplementedError
        else:
            left.emit(bytecode)
            bytecode.emit('CALL')

Comma = create_binary_op('COMMA')


class Conditional(Expression):
    def __init__(self, pos, condition, truepart, falsepart):
        self.pos = pos
        self.condition = condition
        self.truepart = truepart
        self.falsepart = falsepart


class Member(Expression):
    "this is for object[name]"
    def __init__(self, pos, left, expr):
        self.pos = pos
        self.left = left
        self.expr = expr

    def __repr__(self):
        return "Member %s[%s]" % (repr(self.left), repr(self.expr))

    def emit(self, bytecode):
        self.expr.emit(bytecode)
        self.left.emit(bytecode)
        bytecode.emit('LOAD_MEMBER')


class MemberDot(Expression):
    "this is for object.name"
    def __init__(self, pos, left, name):
        self.name = unicode(name.get_literal())
        self.left = left
        self.pos = pos
        self.expr = String(pos, self.name)

    def __repr__(self):
        return "MemberDot %s.%s" % (repr(self.left), self.name)

    def emit(self, bytecode):
        bytecode.emit_str(self.name)
        self.left.emit(bytecode)
        bytecode.emit('LOAD_MEMBER_DOT')


class FunctionStatement(Statement):
    def __init__(self, pos, name, index, body_ast, symbol_map):
        self.pos = pos
        self.name = name
        self.index = index
        self.body_ast = body_ast
        self.symbol_map = symbol_map

    def emit(self, bytecode):
        from jscode import ast_to_bytecode
        body_code = ast_to_bytecode(self.body_ast, self.symbol_map)
        body_code.emit('LOAD_UNDEFINED')

        from js.functions import JsFunction
        name = self.name
        jsfunc = JsFunction(name, body_code)

        index = self.index

        bytecode.emit('LOAD_FUNCTION', jsfunc)
        if index is not None:
            bytecode.emit('STORE', index, name)


class Identifier(Expression):
    def __init__(self, pos, name, index):
        self.pos = pos
        self.name = name
        self.index = index

    def __repr__(self):
        return "Identifier '%s'@%d" % (self.name, self.index)

    def emit(self, bytecode):
        bytecode.emit('LOAD_VARIABLE', self.index, self.name)

    def get_literal(self):
        return self.name


class This(Identifier):
    def __init__(self, pos):
        self.pos = pos

    def emit(self, bytecode):
        bytecode.emit('LOAD_THIS')


class If(Statement):
    def __init__(self, pos, condition, thenpart, elsepart=None):
        self.pos = pos
        self.condition = condition
        self.thenPart = thenpart
        self.elsePart = elsepart

    def emit(self, bytecode):
        self.condition.emit(bytecode)
        endif = bytecode.prealocate_label()
        endthen = bytecode.prealocate_label()
        bytecode.emit('JUMP_IF_FALSE', endthen)
        self.thenPart.emit(bytecode)
        bytecode.emit('JUMP', endif)
        bytecode.emit('LABEL', endthen)

        if self.elsePart is not None:
            self.elsePart.emit(bytecode)
        else:
            bytecode.emit('LOAD_UNDEFINED')

        bytecode.emit('LABEL', endif)


class Switch(Statement):
    def __init__(self, pos, expression, clauses, default_clause):
        self.pos = pos
        self.expression = expression
        self.clauses = clauses
        self.default_clause = default_clause

    def emit(self, bytecode):
        end_of_switch = bytecode.prealocate_label()

        for clause in self.clauses:
            clause_code = bytecode.prealocate_label()
            next_clause = bytecode.prealocate_label()
            for expression in clause.expressions:
                expression.emit(bytecode)
                self.expression.emit(bytecode)
                bytecode.emit('EQ')
                bytecode.emit('JUMP_IF_TRUE', clause_code)

            bytecode.emit('JUMP', next_clause)
            bytecode.emit('LABEL', clause_code)
            clause.block.emit(bytecode)
            bytecode.emit('JUMP', end_of_switch)
            bytecode.emit('LABEL', next_clause)
        self.default_clause.emit(bytecode)
        bytecode.emit('LABEL', end_of_switch)


class CaseBlock(Statement):
    def __init__(self, pos, clauses, default_clause):
        self.pos = pos
        self.clauses = clauses
        self.default_clause = default_clause


class CaseClauses(Statement):
    def __init__(self, pos, clauses):
        self.pos = pos
        self.clauses = clauses


class CaseClause(Statement):
    def __init__(self, pos, expressions, block):
        self.pos = pos
        self.expressions = expressions
        self.block = block


class StatementList(Statement):
    def __init__(self, pos, block):
        self.pos = pos
        self.block = block

    def emit(self, bytecode):
        self.block.emit(bytecode)


class DefaultClause(Statement):
    def __init__(self, pos, block):
        self.pos = pos
        self.block = block

    def emit(self, bytecode):
        self.block.emit(bytecode)

#class Group(UnaryOp):
#    def eval(self, ctx):
#        return self.expr.eval(ctx)

##############################################################################
#
# Binary logic comparison ops and suporting abstract operation
#
##############################################################################


class And(Expression):
    def __init__(self, pos, left, right):
        self.pos = pos
        self.left = left
        self.right = right

    def emit(self, bytecode):
        self.left.emit(bytecode)
        one = bytecode.prealocate_label()
        bytecode.emit('JUMP_IF_FALSE_NOPOP', one)
        self.right.emit(bytecode)
        bytecode.emit('LABEL', one)


class Or(Expression):
    def __init__(self, pos, left, right):
        self.pos = pos
        self.left = left
        self.right = right

    def emit(self, bytecode):
        self.left.emit(bytecode)
        one = bytecode.prealocate_label()
        bytecode.emit('JUMP_IF_TRUE_NOPOP', one)
        self.right.emit(bytecode)
        bytecode.emit('LABEL', one)

Ge = create_binary_op('GE')
Gt = create_binary_op('GT')
Le = create_binary_op('LE')
Lt = create_binary_op('LT')

##############################################################################
#
# Bitwise shifts
#
##############################################################################

Ursh = create_binary_op('URSH')
Rsh = create_binary_op('RSH')
Lsh = create_binary_op('LSH')

##############################################################################
#
# Equality and unequality (== and !=)
#
##############################################################################

Eq = create_binary_op('EQ')
Ne = create_binary_op('NE')

##############################################################################
#
# Strict Equality and unequality, usually means same place in memory
# or equality for primitive values
#
##############################################################################

StrictEq = create_binary_op('IS')
StrictNe = create_binary_op('ISNOT')

In = create_binary_op('IN')
InstanceOf = create_binary_op('INSTANCEOF')


class Typeof(Expression):
    def __init__(self, pos, left):
        self.pos = pos
        self.left = left

    def emit(self, bytecode):
        # obscure hack to be compatible
        if isinstance(self.left, Identifier):
            bytecode.emit('TYPEOF_VARIABLE', self.left.index, self.left.name)
        else:
            self.left.emit(bytecode)
            bytecode.emit('TYPEOF')


class Delete(Expression):
    def __init__(self, pos, what):
        self.pos = pos
        self.what = what

    def emit(self, bytecode):
        what = self.what
        if isinstance(what, Identifier):
            bytecode.emit('DELETE', what.name, what.index)
        elif isinstance(what, MemberDot):
            what.left.emit(bytecode)
            # XXX optimize
            bytecode.emit('LOAD_STRINGCONSTANT', what.name)
            bytecode.emit('DELETE_MEMBER')
        elif isinstance(what, Member):
            what.left.emit(bytecode)
            what.expr.emit(bytecode)
            bytecode.emit('DELETE_MEMBER')
        else:
            what.left.emit(bytecode)
            bytecode.emit('LOAD_BOOLCONSTANT', True)

#class Index(BinaryOp):
#    def eval(self, ctx):
#        w_obj = self.left.eval(ctx).GetValue().ToObject(ctx)
#        name= self.right.eval(ctx).GetValue().to_string(ctx)
#        return W_Reference(name, w_obj)


class ArgumentList(ListOp):
    def emit(self, bytecode):
        for node in self.nodes:
            node.emit(bytecode)
        bytecode.emit('LOAD_LIST', len(self.nodes))

##############################################################################
#
# Math Ops
#
##############################################################################

Plus = create_binary_op('ADD')
Mult = create_binary_op('MUL')
Mod = create_binary_op('MOD')
Division = create_binary_op('DIV')
Sub = create_binary_op('SUB')


class Null(Expression):
    def emit(self, bytecode):
        bytecode.emit('LOAD_NULL')

##############################################################################
#
# Value and object creation
#
##############################################################################


class New(Expression):
    def __init__(self, pos, left):
        self.pos = pos
        self.left = left

    def emit(self, bytecode):
        self.left.emit(bytecode)
        bytecode.emit('NEW_NO_ARGS')


class NewWithArgs(Expression):
    def __init__(self, pos, left, right):
        self.pos = pos
        self.left = left
        self.right = right

    def emit(self, bytecode):
        self.left.emit(bytecode)
        self.right.emit(bytecode)
        bytecode.emit('NEW')


class BaseNumber(Expression):
    pass


class IntNumber(BaseNumber):
    def __init__(self, pos, num):
        self.pos = pos
        self.num = num

    def __repr__(self):
        return "IntNumber %d" % (self.num)

    def emit(self, bytecode):
        bytecode.emit('LOAD_INTCONSTANT', self.num)


class FloatNumber(BaseNumber):
    def __init__(self, pos, num):
        self.pos = pos
        self.num = num

    def emit(self, bytecode):
        bytecode.emit('LOAD_FLOATCONSTANT', self.num)


@enforceargs(unicode)
def string_unquote(string):
    s = string
    if s.startswith('"'):
        assert s.endswith('"')
    else:
        assert s.startswith("'")
        assert s.endswith("'")
    s = s[:-1]
    s = s[1:]

    return s


class String(Expression):
    @enforceargs(None, None, unicode)
    def __init__(self, pos, strval):
        self.pos = pos
        self.strval = strval

    def __repr__(self):
        return "String %s" % (self.strval)

    def emit(self, bytecode):
        strval = self.strval
        bytecode.emit('LOAD_STRINGCONSTANT', strval)


class ObjectInit(ListOp):
    def emit(self, bytecode):
        for prop in self.nodes:
            prop.emit(bytecode)
        bytecode.emit('LOAD_OBJECT', len(self.nodes))


class SourceElements(Statement):
    """
    SourceElements nodes are found on each function declaration and in global code
    """
    def __init__(self, pos, var_decl, func_decl, nodes, sourcename=''):
        self.pos = pos
        self.var_decl = var_decl
        self.func_decl = func_decl
        self.nodes = nodes
        self.sourcename = sourcename

    def emit(self, bytecode):
        functions = self.func_decl.values()
        nodes = self.nodes

        for funccode in functions:
            funccode.emit(bytecode)
            bytecode.emit('POP')

        if len(nodes) > 1:
            for node in nodes[:-1]:
                node.emit(bytecode)
                bytecode.emit('POP')

        if len(nodes) > 0:
            node = nodes[-1]
            node.emit(bytecode)
        else:
            bytecode.emit('LOAD_UNDEFINED')


class Program(Statement):
    def __init__(self, pos, body, symbol_map):
        self.pos = pos
        self.body = body
        self.symbol_map = symbol_map

    def emit(self, bytecode):
        self.body.emit(bytecode)


class Return(Statement):
    def __init__(self, pos, expr):
        self.pos = pos
        self.expr = expr

    def emit(self, bytecode):
        if self.expr is None:
            bytecode.emit('LOAD_UNDEFINED')
        else:
            self.expr.emit(bytecode)
        bytecode.emit('RETURN')


class Throw(Statement):
    def __init__(self, pos, exp):
        self.pos = pos
        self.exp = exp

    def emit(self, bytecode):
        self.exp.emit(bytecode)
        bytecode.emit('THROW')


class Try(Statement):
    def __init__(self, pos, tryblock, catchparam, catchblock, finallyblock):
        self.pos = pos
        self.tryblock = tryblock
        self.catchparam = catchparam
        self.catchblock = catchblock
        self.finallyblock = finallyblock

    def emit(self, bytecode):
        from js.jscode import JsCode
        from js.functions import JsExecutableCode

        trycode = JsCode()
        self.tryblock.emit(trycode)

        tryexec = JsExecutableCode(trycode)

        if self.catchblock:
            catchcode = JsCode()
            self.catchblock.emit(catchcode)
            catchexec = JsExecutableCode(catchcode)
            catchparam = self.catchparam.get_literal()
        else:
            catchexec = None
            catchparam = None

        if self.finallyblock:
            finallycode = JsCode()
            self.finallyblock.emit(finallycode)
            finallyexec = JsExecutableCode(finallycode)
        else:
            finallyexec = None
        bytecode.emit('TRYCATCHBLOCK', tryexec, catchparam, catchexec, finallyexec)


class VariableDeclaration(Expression):
    def __init__(self, pos, identifier, index, expr=None):
        self.pos = pos
        self.identifier = identifier.get_literal()
        assert identifier is not None
        self.expr = expr
        assert index is not None
        self.index = index

    def emit(self, bytecode):
        if self.expr is not None:
            self.expr.emit(bytecode)
            bytecode.emit('STORE', self.index, self.identifier)
        else:
            # variable declaration actualy does nothing
            bytecode.emit('LOAD_UNDEFINED')

    def __str__(self):
        return "VariableDeclaration %s:%s" % (self.identifier, self.expr)

#class LocalVariableDeclaration(Expression):
#    def __init__(self, pos, identifier, local, expr=None):
#        self.pos = pos
#        self.identifier = identifier.get_literal()
#        self.local = local
#        self.expr = expr
#
#    def emit(self, bytecode):
#        if self.expr is not None:
#            self.expr.emit(bytecode)
#            bytecode.emit('STORE_LOCAL', self.local)
#
#    def __repr__(self):
#        return "LocalVariableDeclaration %d(%s):%s" % (self.local, self.identifier, self.expr)

#class LocalIdentifier(Expression):
#    def __init__(self, pos, identifier, local):
#        self.pos = pos
#        self.identifier = identifier
#        self.local = local
#
#    def emit(self, bytecode):
#        bytecode.emit('LOAD_LOCAL', self.local)
#
#    def get_literal(self):
#        return self.identifier
#
#    def get_local(self):
#        return self.local


class VariableDeclList(Statement):
    def __init__(self, pos, nodes):
        self.pos = pos
        self.nodes = nodes

    def emit(self, bytecode):
        nodes = self.nodes
        if len(nodes) > 1:
            for node in nodes[:-1]:
                node.emit(bytecode)
                bytecode.emit('POP')

        if len(nodes) > 0:
            node = nodes[-1]
            node.emit(bytecode)
        else:
            bytecode.emit('LOAD_UNDEFINED')


class Variable(Statement):
    def __init__(self, pos, body):
        self.pos = pos
        self.body = body

    def emit(self, bytecode):
        self.body.emit(bytecode)


class Empty(Expression):
    def __init__(self, pos):
        self.pos = pos

    def emit(self, bytecode):
        pass


class Void(Expression):
    def __init__(self, pos, expr):
        self.pos = pos
        self.expr = expr

    def emit(self, bytecode):
        self.expr.emit(bytecode)
        bytecode.emit('POP')
        bytecode.emit('LOAD_UNDEFINED')


class EmptyExpression(Expression):
    def emit(self, bytecode):
        bytecode.emit('LOAD_UNDEFINED')


class With(Statement):
    def __init__(self, pos, expr, body):
        self.pos = pos
        self.expr = expr
        self.body = body

    def emit(self, bytecode):
        from js.jscode import JsCode
        from js.functions import JsExecutableCode

        self.expr.emit(bytecode)

        body_code = JsCode()
        self.body.emit(body_code)
        body_exec = JsExecutableCode(body_code)

        bytecode.emit('WITH', body_exec)


class WhileBase(Statement):
    def __init__(self, pos, condition, body):
        self.pos = pos
        self.condition = condition
        self.body = body


class Do(WhileBase):
    def emit(self, bytecode):
        startlabel = bytecode.emit_startloop_label()
        end = bytecode.prealocate_endloop_label()
        self.body.emit(bytecode)
        self.condition.emit(bytecode)
        bytecode.emit('JUMP_IF_FALSE', end)
        bytecode.emit('POP')
        bytecode.emit('JUMP', startlabel)
        bytecode.emit_endloop_label(end)


class While(WhileBase):
    def emit(self, bytecode):
        bytecode.emit('LOAD_UNDEFINED')
        startlabel = bytecode.emit_startloop_label()
        bytecode.continue_at_label(startlabel)
        self.condition.emit(bytecode)
        endlabel = bytecode.prealocate_endloop_label()
        bytecode.emit('JUMP_IF_FALSE', endlabel)
        bytecode.emit('POP')
        self.body.emit(bytecode)
        bytecode.emit('JUMP', startlabel)
        bytecode.emit_endloop_label(endlabel)
        bytecode.done_continue()


class ForIn(Statement):
    def __init__(self, pos, left_expr, lobject, body):
        self.pos = pos
        self.left_expr = left_expr
        self.w_object = lobject
        self.body = body

    def emit(self, bytecode):
        w_object = self.w_object
        left_expr = self.left_expr
        body = self.body

        w_object.emit(bytecode)
        bytecode.emit('LOAD_ITERATOR')
        # load the "last" iterations result
        bytecode.emit('LOAD_UNDEFINED')
        precond = bytecode.emit_startloop_label()
        finish = bytecode.prealocate_endloop_label(True)

        bytecode.emit('JUMP_IF_ITERATOR_EMPTY', finish)

        # put next iterator value on stack
        bytecode.emit('NEXT_ITERATOR')

        # store iterrator value into approperiate place
        if isinstance(left_expr, This):
            raise JsException(u'Invalid left-hand side in for-in')
        if isinstance(left_expr, Identifier):
            name = left_expr.name
            index = left_expr.index
            bytecode.emit('STORE', index, name)
            bytecode.emit('POP')
        elif isinstance(left_expr, VariableDeclaration):
            name = left_expr.identifier
            index = left_expr.index
            bytecode.emit('STORE', index, name)
            bytecode.emit('POP')
        elif isinstance(left_expr, MemberDot):
            bytecode.emit('LOAD_STRINGCONSTANT', left_expr.name)
            left_expr.left.emit(bytecode)
            bytecode.emit('STORE_MEMBER')
            bytecode.emit('POP')

        elif isinstance(left_expr, Member):
            left_expr.expr.emit(bytecode)
            left_expr.left.emit(bytecode)
            bytecode.emit('STORE_MEMBER')
            bytecode.emit('POP')
        else:
            raise JsTypeError(u'unsupported')

        body.emit(bytecode)
        bytecode.emit('JUMP', precond)
        bytecode.emit_endloop_label(finish)


class For(Statement):
    def __init__(self, pos, setup, condition, update, body):
        self.pos = pos
        self.setup = setup
        self.condition = condition
        self.update = update
        self.body = body

    def emit(self, bytecode):
        self.setup.emit(bytecode)
        if isinstance(self.setup, Expression) or isinstance(self.setup, VariableDeclList):
            bytecode.emit('POP')
        bytecode.emit('LOAD_UNDEFINED')
        precond = bytecode.emit_startloop_label()
        finish = bytecode.prealocate_endloop_label()
        update = bytecode.prealocate_updateloop_label()
        self.condition.emit(bytecode)
        bytecode.emit('JUMP_IF_FALSE', finish)
        bytecode.emit('POP')
        self.body.emit(bytecode)
        bytecode.emit_updateloop_label(update)
        self.update.emit(bytecode)
        bytecode.emit('POP')
        bytecode.emit('JUMP', precond)
        bytecode.emit_endloop_label(finish)


class Boolean(Expression):
    def __init__(self, pos, boolval):
        self.pos = pos
        self.bool = boolval

    def emit(self, bytecode):
        bytecode.emit('LOAD_BOOLCONSTANT', self.bool)

Not = create_unary_op('NOT')
UMinus = create_unary_op('UMINUS')
UPlus = create_unary_op('UPLUS')

unrolling_classes = unrolling_iterable((If, Return, Block, While))
