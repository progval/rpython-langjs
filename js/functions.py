from js.opcodes import BaseJump

class JsBaseFunction(object):
    eval_code = False
    function_code = False
    configurable_bindings = False
    strict = False

    def __init__(self):
        pass

    def run(self, ctx):
        raise NotImplementedError

    def estimated_stack_size(self):
        return 2

    def to_string(self):
        return 'function() {}'

    def variables(self):
        return []

    def functions(self):
        return []

    #def index_for_symbol(self, symbol):
        #return None

    #def symbols(self):
        #return []

    #def symbol_for_index(self, index):
        #return None

    def params(self):
        return []

    def name(self):
        return '_unnamed_'

    def is_eval_code(self):
        return False

    def is_function_code(self):
        return False

class JsNativeFunction(JsBaseFunction):
    def __init__(self, function, name = None):
        JsBaseFunction.__init__(self)
        self._name_ = name
        self._function_ = function

    def name(self):
        return self._name_

    def run(self, ctx):
        args = ctx.argv()
        this = ctx.this_binding()
        return self._function_(this, args)

    def to_string(self):
        name = self.name()
        if name is not None:
            return 'function %s() { [native code] }' % (name, )
        else:
            return 'function () { [native code] }'

class JsIntimateFunction(JsNativeFunction):
    def run(self, ctx):
        return self._function_(ctx)

class JsExecutableCode(JsBaseFunction):
    def __init__(self, js_code):
        JsBaseFunction.__init__(self)
        self._js_code_ = js_code
        self.stack_size = js_code.estimated_stack_size()
        self.opcodes = self._opcodes_from_code_()

    def _opcodes_from_code_(self):
        return self._js_code_.to_executable_opcodes()

    #def estimated_stack_size(self):
        #return self.stack_size

    def _get_opcode(self, pc):
        assert pc >= 0
        return self.opcodes[pc]

    def run(self, ctx):
        pc = 0
        while True:
            if pc >= len(self.opcodes):
                break
            opcode = self._get_opcode(pc)
            result = opcode.eval(ctx)
            assert result is None
            #print('pc:%d, opcode:%s, stack:%s'%(pc, repr(opcode), str(ctx._stack_)))

            from js.opcodes import RETURN
            if isinstance(opcode, BaseJump):
                new_pc = opcode.do_jump(ctx, pc)
                pc = new_pc
                continue
            elif isinstance(opcode, RETURN):
                break
            else:
                pc += 1

        return ctx.stack_top()

    def variables(self):
        return self._js_code_.variables()

    def functions(self):
        return self._js_code_.functions()

    #def index_for_symbol(self, symbol):
        #return self._js_code_.index_for_symbol(symbol)

    #def symbols(self):
        #return self._js_code_.symbols()

    #def symbol_for_index(self, index):
        #return self._js_code_.symbol_for_index(index)

    def params(self):
        return self._js_code_.params()

    def name(self):
        return '_unnamed_'

    def to_string(self):
        name = self.name()
        if name is not None:
            return 'function %s() { }' % (name, )
        else:
            return 'function () { }'

class JsGlobalCode(JsExecutableCode):
    def _opcodes_from_code_(self):
        return self._js_code_.to_global_opcodes()

class JsEvalCode(JsExecutableCode):
    def _opcodes_from_code_(self):
        return self._js_code_.to_global_opcodes()

    def is_eval_code(self):
        return True

class JsFunction(JsExecutableCode):
    #_immutable_fields_ = ["opcodes[*]", 'name', 'params', 'code', 'scope']

    def __init__(self, name, js_code):
        JsExecutableCode.__init__(self, js_code)
        self._name_ = name

    def _opcodes_from_code_(self):
        return self._js_code_.to_function_opcodes()
        #self.opcodes = make_sure_not_resized(code.opcodes[:])

    def name(self):
        return self._name_

    def is_function_code(self):
        return True

    #@jit.unroll_safe
    #def run(self, ctx, args=[], this=None):
        #from js.jsexecution_context import make_activation_context, make_function_context

        #from js.jsobj import W_Arguments, w_Undefined
        #w_Arguments = W_Arguments(self, args)
        #act = make_activation_context(ctx, this, w_Arguments)
        #newctx = make_function_context(act, self)

        #paramn = len(self.params)
        #for i in range(paramn):
            #paramname = self.params[i]
            #try:
                #value = args[i]
            #except IndexError:
                #value = w_Undefined
            #newctx.declare_variable(paramname)
            #newctx.assign(paramname, value)

        #return self._run_with_context(ctx=newctx, save_stack = False)

    #def _run_with_context(self, ctx, check_stack=True, save_stack=True):
        #state = ([], 0)
        #if save_stack:
            #state = _save_stack(ctx, self.estimated_stack_size())

        #try:
            #self._run_bytecode(ctx)
            #if check_stack:
                #ctx.check_stack()
            #return ctx.top()
        #except ReturnException, e:
            #return e.value
        #finally:
            #if save_stack:
                #_restore_stack(ctx, state)

    #def _run_bytecode(self, ctx, pc=0):
        #while True:
            #jitdriver.jit_merge_point(pc=pc, self=self, ctx=ctx)
            #if pc >= len(self.opcodes):
                #break

            #opcode = self._get_opcode(pc)
            ##if we_are_translated():
            ##    #this is an optimization strategy for translated code
            ##    #on top of cpython it destroys the performance
            ##    #besides, this code might be completely wrong
            ##    for name, op in opcode_unrolling:
            ##        opcode = hint(opcode, deepfreeze=True)
            ##        if isinstance(opcode, op):
            ##            result = opcode.eval(ctx, stack)
            ##            assert result is None
            ##            break
            ##else:
            #result = opcode.eval(ctx)
            #assert result is None

            #if isinstance(opcode, BaseJump):
                #new_pc = opcode.do_jump(ctx, pc)
                #condition = new_pc < pc
                #pc = new_pc
                #if condition:
                    #jitdriver.can_enter_jit(pc=pc, self=self, ctx=ctx)
                #continue
            #else:
                #pc += 1

            #if isinstance(opcode, WITH_START):
                #pc = self._run_bytecode(opcode.newctx, pc)
            #elif isinstance(opcode, WITH_END):
                #break

        #return pc
