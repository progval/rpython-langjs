from pypy.rlib.jit import hint
from pypy.rlib.objectmodel import we_are_translated
from pypy.rlib.jit import JitDriver, purefunction

from js.execution import JsTypeError, ReturnException, ThrowException
from js.opcodes import opcodes, POP, LABEL, BaseJump, WITH_START, WITH_END
from js.jsobj import W_Root, W_String

def get_printable_location(pc, jsfunction):
    return str(jsfunction.opcodes[pc])

jitdriver = JitDriver(greens=['pc', 'self'], reds=['to_pop', 'stack', 'ctx'], get_printable_location = get_printable_location, virtualizables=['stack'])

class AlreadyRun(Exception):
    pass

class Stack(object):
    _virtualizable2_ = ['content[*]', 'pointer']
    def __init__(self, size):
        self = hint(self, access_directly = True, fresh_virtualizable = True)
        self.content = [None] * size
        self.pointer = 0

    def __repr__(self):
        return "Stack %(content)s@%(pointer)d" % {'pointer': self.pointer, 'content': self.content}

    def pop(self):
        e = self.top()
        i = self.pointer - 1
        assert i >= 0
        self.content[i] = None
        self.pointer = i
        return e

    def top(self):
        i = self.pointer - 1
        if i < 0:
            raise IndexError
        return self.content[i]

    def append(self, element):
        assert isinstance(element, W_Root)
        i = self.pointer
        assert i >= 0
        self.content[i] = element
        self.pointer = i + 1

    def pop_n(self, n):
        list = []
        for i in xrange(0, n):
            list.append(self.pop())
        list.reverse()
        return list

    def check(self):
        assert self.pointer == 1

class JsCode(object):
    """ That object stands for code of a single javascript function
    """
    def __init__(self):
        self.opcodes = []
        self.label_count = 0
        self.has_labels = True
        self.startlooplabel = []
        self.endlooplabel = []
        self.updatelooplabel = []

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



    def unpop(self):
        if self.opcodes and isinstance(self.opcodes[-1], POP):
            self.opcodes.pop()
            return True
        else:
            return False

    def unpop_or_undefined(self):
        if not self.unpop():
            self.emit('LOAD_UNDEFINED')

    def make_js_function(self, name='__dont_care__', params=None):
        self.unpop_or_undefined()

        if self.has_labels:
            self.remove_labels()

        return JsFunction(name, params, self.opcodes[:])

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

    def __repr__(self):
        return "\n".join([repr(i) for i in self.opcodes])

class JsFunction(object):
    _immutable_fields_ = ["opcodes[*]"]

    def __init__(self, name, params, code):
        from pypy.rlib.debug import make_sure_not_resized
        self.name = name
        self.params = params
        self.opcodes = make_sure_not_resized(code)

    def run(self, ctx, check_stack=True):
        stack = Stack(len(self.opcodes) * 2)
        try:
            return self.run_bytecode(ctx, stack, check_stack)
        except ReturnException, e:
            return e.value

    def _get_opcode(self, pc):
        assert pc >= 0
        return self.opcodes[pc]

    def run_bytecode(self, ctx, stack, check_stack=True):
        pc = 0
        to_pop = 0
        try:
            while True:
                jitdriver.jit_merge_point(pc=pc, stack=stack, self=self, ctx=ctx, to_pop=to_pop)
                if pc >= len(self.opcodes):
                    break

                opcode = self._get_opcode(pc)
                #if we_are_translated():
                #    #this is an optimization strategy for translated code
                #    #on top of cpython it destroys the performance
                #    #besides, this code might be completely wrong
                #    for name, op in opcode_unrolling:
                #        opcode = hint(opcode, deepfreeze=True)
                #        if isinstance(opcode, op):
                #            result = opcode.eval(ctx, stack)
                #            assert result is None
                #            break
                #else:
                result = opcode.eval(ctx, stack)
                assert result is None

                if isinstance(opcode, BaseJump):
                    new_pc = opcode.do_jump(stack, pc)
                    condition = new_pc < pc
                    pc = new_pc
                    if condition:
                        jitdriver.can_enter_jit(pc=pc, stack=stack, self=self, ctx=ctx, to_pop=to_pop)
                    continue
                else:
                    pc += 1
                if isinstance(opcode, WITH_START):
                    to_pop += 1
                elif isinstance(opcode, WITH_END):
                    to_pop -= 1
        finally:
            for i in range(to_pop):
                ctx.pop_object()

        if check_stack:
            stack.check()
        return stack.top()
