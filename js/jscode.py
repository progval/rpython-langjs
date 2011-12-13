from pypy.rlib.jit import hint
from pypy.rlib.objectmodel import we_are_translated
from pypy.rlib.jit import JitDriver, purefunction

from js.execution import JsTypeError, ReturnException, ThrowException
from js.opcodes import opcodes, LABEL, BaseJump, WITH_START, WITH_END
from js.jsobj import W_Root, W_String, _w

from pypy.rlib import jit, debug

def get_printable_location(pc, jsfunction):
    try:
        return str(jsfunction.opcodes[pc])
    except IndexError:
        return "???"

jitdriver = JitDriver(greens=['pc', 'self'], reds=['ctx'], get_printable_location = get_printable_location, virtualizables=['ctx'])

class AlreadyRun(Exception):
    pass

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
        from js.astbuilder import Scope
        self.scope = Scope()
        self._estimated_stack_size = -1

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

    def unpop_or_undefined(self):
        if not self.unpop():
            self.emit('LOAD_UNDEFINED')
        #elif not self.returns():
            #self.emit('LOAD_UNDEFINED')

    def make_js_function(self, name='__dont_care__', params=[]):
        self.unpop_or_undefined()

        if self.has_labels:
            self.remove_labels()

        return JsFunction(name, params, self)

    def ToJsFunction(self, name='__dont_care__', params=[]):
        return self.make_js_function(name, params)

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

@jit.dont_look_inside
def _save_stack(ctx, size):
    old_stack = ctx.stack
    old_stack_pointer = ctx.stack_pointer

    ctx._init_stack(size)
    return old_stack, old_stack_pointer

@jit.dont_look_inside
def _restore_stack(ctx, state):
    old_stack, old_stack_pointer = state
    ctx.stack_pointer = old_stack_pointer
    ctx.stack = old_stack

class Js__Function(object):
    name = 'anonymous'
    code = ''
    params = []

    def run(self, ctx, args=[], this=None):
        raise NotImplementedError

    def estimated_stack_size(self):
        return 2

    def local_variables(self):
        return None

    def ToString(self):
        if self.name is not None:
            return 'function %s() { [native code] }' % (self.name, )
        else:
            return 'function () { [native code] }'

class Js_NativeFunction(Js__Function):
    def __init__(self, function, name = None):
        if name is not None:
            self.name = name
        self._function_ = _native_function(function)

    def run(self, ctx, args=[], this=None):
        return self._function_(this, args)

    def ToString(self):
        if self.name is not None:
            return 'function %s() { [native code] }' % (self.name, )
        else:
            return 'function () { [native code] }'

def _native_function(fn):
    from js.jsobj import _w
    def f(this, args):
        res = fn(this, *args)
        return _w(res)
    return f

class JsFunction(Js__Function):
    _immutable_fields_ = ["opcodes[*]", 'name', 'params', 'code', 'scope']

    def __init__(self, name, params, code):
        Js__Function.__init__(self)
        from pypy.rlib.debug import make_sure_not_resized
        self.name = name
        self.params = params
        self._code_ = code
        self.opcodes = make_sure_not_resized(code.opcodes[:])
        self.scope = code.scope

    def estimated_stack_size(self):
        return self._code_.estimated_stack_size()

    def local_variables(self):
        if self.scope:
            return self.scope.local_variables

    def ToString(self):
        return 'function () {}'

    def _get_opcode(self, pc):
        assert pc >= 0
        return self.opcodes[pc]

    @jit.unroll_safe
    def run(self, ctx, args=[], this=None):
        from js.jsexecution_context import make_activation_context, make_function_context

        from js.jsobj import W_Arguments, w_Undefined
        w_Arguments = W_Arguments(self, args)
        act = make_activation_context(ctx, this, w_Arguments)
        newctx = make_function_context(act, self)

        paramn = len(self.params)
        for i in range(paramn):
            paramname = self.params[i]
            try:
                value = args[i]
            except IndexError:
                value = w_Undefined
            newctx.declare_variable(paramname)
            newctx.assign(paramname, value)

        return self._run_with_context(ctx=newctx, save_stack = False)

    def _run_with_context(self, ctx, check_stack=True, save_stack=True):
        state = ([], 0)
        if save_stack:
            state = _save_stack(ctx, self.estimated_stack_size())

        try:
            self._run_bytecode(ctx)
            if check_stack:
                ctx.check_stack()
            return ctx.top()
        except ReturnException, e:
            return e.value
        finally:
            if save_stack:
                _restore_stack(ctx, state)

    def _run_bytecode(self, ctx, pc=0):
        while True:
            jitdriver.jit_merge_point(pc=pc, self=self, ctx=ctx)
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
            result = opcode.eval(ctx)
            assert result is None

            if isinstance(opcode, BaseJump):
                new_pc = opcode.do_jump(ctx, pc)
                condition = new_pc < pc
                pc = new_pc
                if condition:
                    jitdriver.can_enter_jit(pc=pc, self=self, ctx=ctx)
                continue
            else:
                pc += 1

            if isinstance(opcode, WITH_START):
                pc = self._run_bytecode(opcode.newctx, pc)
            elif isinstance(opcode, WITH_END):
                break

        return pc
