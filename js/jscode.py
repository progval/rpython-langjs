from pypy.rlib.jit import hint
from pypy.rlib.objectmodel import we_are_translated
from pypy.rlib.jit import JitDriver, purefunction

from js.execution import JsTypeError, ReturnException, ThrowException, JsReferenceError
from js.opcodes import opcodes, LABEL, BaseJump
from js.jsobj import W_Root, W_String, _w, w_Null, w_Undefined

from pypy.rlib import jit, debug

def get_printable_location(pc, jsfunction):
    try:
        return str(jsfunction.opcodes[pc])
    except IndexError:
        return "???"

#jitdriver = JitDriver(greens=['pc', 'self'], reds=['ctx'], get_printable_location = get_printable_location, virtualizables=['ctx'])

def ast_to_bytecode(ast, symbol_map):
    bytecode = JsCode(symbol_map)
    if ast is not None:
        ast.emit(bytecode)
    return bytecode

class AlreadyRun(Exception):
    pass

from js.astbuilder import empty_symbols

class JsCode(object):
    """ That object stands for code of a single javascript function
    """
    def __init__(self, symbol_map = empty_symbols):
        self.opcodes = []
        self.label_count = 0
        self.has_labels = True
        self.startlooplabel = []
        self.endlooplabel = []
        self.updatelooplabel = []
        self._estimated_stack_size = -1
        self._symbols = symbol_map

    def variables(self):
        return self._symbols.variables

    def functions(self):
        return self._symbols.functions

    def index_for_symbol(self, symbol):
        return self._symbols.get_index(symbol)

    def symbols(self):
        return self._symbols.get_symbols()

    def symbol_for_index(self, index):
        return self._symbols.get_symbol(index)

    def params(self):
        return self._symbols.parameters

    @jit.elidable
    def estimated_stack_size(self):
        # TODO: compute only once
        if self._estimated_stack_size == -1:
            max_size = 0
            moving_size = 0
            for opcode in self.opcodes:
                moving_size += opcode.stack_change()
                max_size = max(moving_size, max_size)
            assert max_size >= 0
            self._estimated_stack_size = max_size

        return self._estimated_stack_size

    def emit_label(self, num = -1):
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

    def prealocate_endloop_label(self):
        num = self.prealocate_label()
        self.endlooplabel.append(num)
        return num

    def prealocate_updateloop_label(self):
        num = self.prealocate_label()
        self.updatelooplabel.append(num)
        return num

    def emit_endloop_label(self, label):
        self.endlooplabel.pop()
        self.startlooplabel.pop()
        self.emit_label(label)

    def emit_updateloop_label(self, label):
        self.updatelooplabel.pop()
        self.emit_label(label)

    def emit_break(self):
        if not self.endlooplabel:
            raise ThrowException(W_String("Break outside loop"))
        self.emit('JUMP', self.endlooplabel[-1])

    def emit_continue(self):
        if not self.startlooplabel:
            raise ThrowException(W_String("Continue outside loop"))
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

    def unpop_or_undefined(self):
        if not self.unpop():
            self.emit('LOAD_UNDEFINED')
        #elif not self.returns():
            #self.emit('LOAD_UNDEFINED')

    def to_function_opcodes(self):
        self.unlabel()
        #self.unpop_or_undefined()
        self.emit('LOAD_UNDEFINED')
        return self.opcodes

    def to_eval_opcodes(self):
        self.unlabel()
        self.unpop_or_undefined()
        return self.opcodes

    def to_global_opcodes(self):
        self.unlabel()
        self.unpop_or_undefined()
        return self.opcodes

    def to_executable_opcodes(self):
        self.unlabel()
        self.unpop()
        return self.opcodes

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

    #def __repr__(self):
        #return "\n".join([repr(i) for i in self.opcodes])

