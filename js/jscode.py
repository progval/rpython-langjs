#from pypy.rlib.jit import hint
#from pypy.rlib.objectmodel import we_are_translated
from rpython.rlib import jit

from js.exception import JsThrowException
from js.opcodes import opcodes, LABEL, BaseJump
from js.jsobj import W_String


def get_printable_location(pc, debug, jscode):
    if pc < jscode._opcode_count():
        opcode = jscode._get_opcode(pc)
        if jscode._function_name_ is not None:
            return '%d: %s function: %s' % (pc, str(opcode), str(jscode._function_name_))
        else:
            return '%d: %s' % (pc, str(opcode))
    else:
        return '%d: %s' % (pc, 'end of opcodes')

jitdriver = jit.JitDriver(greens=['pc', 'debug', 'self'], reds=['result', 'ctx'], get_printable_location=get_printable_location, virtualizables=['ctx'])


def ast_to_bytecode(ast, symbol_map):
    bytecode = JsCode(symbol_map)
    if ast is not None:
        ast.emit(bytecode)
    return bytecode


class AlreadyRun(Exception):
    pass

from js.symbol_map import SymbolMap
empty_symbols = SymbolMap().finalize()


class JsCode(object):
    _immutable_fields_ = ['compiled_opcodes[*]', '_symbols', 'parameters[*]']

    """ That object stands for code of a single javascript function
    """
    def __init__(self, symbol_map=empty_symbols):
        self.opcodes = []
        self.label_count = 0
        self.has_labels = True
        self.startlooplabel = []
        self.endlooplabel = []
        self.pop_after_break = []
        self.updatelooplabel = []
        self._estimated_stack_size = -1
        self._symbols = symbol_map
        self.parameters = symbol_map.parameters[:]
        self._function_name_ = None

    def variables(self):
        return self._symbols.variables

    def functions(self):
        return self._symbols.functions

    def index_for_symbol(self, symbol):
        return self._symbols.get_index(symbol)

    def symbols(self):
        return self._symbols.get_symbols()

    def params(self):
        return self._symbols.parameters

    @jit.elidable
    def estimated_stack_size(self):
        if self._estimated_stack_size == -1:
            max_size = 0
            moving_size = 0
            for opcode in self.compiled_opcodes:
                moving_size += opcode.stack_change()
                max_size = max(moving_size, max_size)
            assert max_size >= 0
            self._estimated_stack_size = max_size

        return jit.promote(self._estimated_stack_size)

    def symbol_size(self):
        return self._symbols.len()

    def emit_label(self, num=-1):
        if num == -1:
            num = self.prealocate_label()
        self.emit('LABEL', num)
        return num

    def emit_startloop_label(self):
        num = self.emit_label()
        self.startlooplabel.append(num)
        return num

    def prealocate_label(self):
        num = self.label_count
        self.label_count += 1
        return num

    def prealocate_endloop_label(self, pop_after_break=False):
        num = self.prealocate_label()
        self.endlooplabel.append(num)
        self.pop_after_break.append(pop_after_break)
        return num

    def prealocate_updateloop_label(self):
        num = self.prealocate_label()
        self.updatelooplabel.append(num)
        return num

    def emit_endloop_label(self, label):
        self.endlooplabel.pop()
        self.startlooplabel.pop()
        self.pop_after_break.pop()
        self.emit_label(label)

    def emit_updateloop_label(self, label):
        self.updatelooplabel.pop()
        self.emit_label(label)

    def emit_break(self):
        if not self.endlooplabel:
            raise JsThrowException(W_String(u"Break outside loop"))
        if self.pop_after_break[-1] is True:
            self.emit('POP')
        self.emit('JUMP', self.endlooplabel[-1])

    def emit_continue(self):
        if not self.startlooplabel:
            raise JsThrowException(W_String(u"Continue outside loop"))
        self.emit('JUMP', self.updatelooplabel[-1])

    def continue_at_label(self, label):
        self.updatelooplabel.append(label)

    def done_continue(self):
        self.updatelooplabel.pop()

    def emit(self, operation, *args):
        opcode = getattr(opcodes, operation)(*args)
        self.opcodes.append(opcode)
        return opcode
    emit._annspecialcase_ = 'specialize:arg(1)'

    def emit_str(self, s):
        return self.emit('LOAD_STRINGCONSTANT', s)

    def emit_int(self, i):
        return self.emit('LOAD_INTCONSTANT', i)

    def unpop(self):
        from js.opcodes import POP
        if self.opcodes and isinstance(self.opcodes[-1], POP):
            self.opcodes.pop()
            return True
        else:
            return False

    def returns(self):
        from js.opcodes import RETURN
        if self.opcodes and isinstance(self.opcodes[-1], RETURN):
            return True
        return False

    def unlabel(self):
        if self.has_labels:
            self.remove_labels()

    def compile(self):
        self.unlabel()
        self.compiled_opcodes = [o for o in self.opcodes]
        self.estimated_stack_size()

    def remove_labels(self):
        """ Basic optimization to remove all labels and change
        jumps to addresses. Necessary to run code at all
        """
        if not self.has_labels:
            raise AlreadyRun("Already has labels")
        labels = {}
        counter = 0
        for i in range(len(self.opcodes)):
            op = self.opcodes[i]
            if isinstance(op, LABEL):
                labels[op.num] = counter
            else:
                counter += 1
        self.opcodes = [op for op in self.opcodes if not isinstance(op, LABEL)]
        for op in self.opcodes:
            if isinstance(op, BaseJump):
                op.where = labels[op.where]
        self.has_labels = False

    @jit.elidable
    def _get_opcode(self, pc):
        assert pc >= 0
        return self.compiled_opcodes[pc]

    @jit.elidable
    def _opcode_count(self):
        return len(self.compiled_opcodes)

    def run(self, ctx):
        from js.object_space import object_space
        debug = object_space.interpreter.config.debug
        from js.completion import NormalCompletion, is_completion, is_return_completion, is_empty_completion
        from js.opcodes import BaseJump

        if self._opcode_count() == 0:
            return NormalCompletion()

        if debug:
            print('start running %s' % (str(self)))

        pc = 0
        result = None
        while True:
            jitdriver.jit_merge_point(pc=pc, debug=debug, self=self, ctx=ctx, result=result)
            if pc >= self._opcode_count():
                break
            opcode = self._get_opcode(pc)
            result = opcode.eval(ctx)

            if debug:
                d = u'%s\t%s' % (unicode(str(pc)), unicode(str(opcode)))
                #d = u'%s' % (unicode(str(pc)))
                #d = u'%3d %25s %s %s' % (pc, unicode(opcode), unicode([unicode(s) for s in ctx._stack_]), unicode(result))
                print(d)

            if is_return_completion(result):
                break
            elif not is_completion(result):
                result = NormalCompletion()

            if isinstance(opcode, BaseJump):
                new_pc = opcode.do_jump(ctx, pc)
                if new_pc < pc:
                    jitdriver.can_enter_jit(pc=pc, debug=debug, self=self, ctx=ctx, result=result)
                pc = new_pc
                continue
            else:
                pc += 1

        assert is_completion(result)
        if is_empty_completion(result):
            result = NormalCompletion(value=ctx.stack_top())

        return result


    #def __repr__(self):
        #return "\n".join([repr(i) for i in self.opcodes])
