from js.jsobj import w_Undefined
from js.utils import StackMixin


class ExecutionContext(StackMixin):
    _immutable_fields_ = ['_stack_', '_stack_resize_', '_this_binding_', '_lexical_environment_', '_variable_environment_']
    _refs_resizable_ = True

    def __init__(self, stack_size=1, refs_size=1):
        self._lexical_environment_ = None
        self._variable_environment_ = None
        self._this_binding_ = None
        self._refs_ = [None] * refs_size
        self._init_stack_(size=stack_size, resize=False)

    def stack_append(self, value):
        self._stack_append(value)

    def stack_pop(self):
        return self._stack_pop()

    def stack_top(self):
        return self._stack_top()

    def stack_pop_n(self, n):
        if n < 1:
            return []

        r = []
        i = n
        while i > 0:
            i -= 1
            e = self._stack_pop()
            r = [e] + r

        return r

    def this_binding(self):
        return self._this_binding_

    def implicit_this_binding(self):
        return self.lexical_environment().environment_record.implicit_this_value()

    def variable_environment(self):
        return self._variable_environment_

    def lexical_environment(self):
        return self._lexical_environment_

    def set_lexical_environment(self, lex_env):
        self._lexical_environment_ = lex_env

    # 10.5
    def declaration_binding_initialization(self):
        env = self._variable_environment_.environment_record
        strict = self._strict_
        code = self._code_

        if code.is_eval_code():
            configurable_bindings = True
        else:
            configurable_bindings = False

        # 4.
        if code.is_function_code():
            names = self._formal_parameters_
            n = 0
            args = self._argument_values_

            arg_count = len(args)
            for arg_name in names:
                n += 1
                if n > arg_count:
                    v = w_Undefined
                else:
                    v = args[n - 1]
                arg_already_declared = env.has_binding(arg_name)
                if arg_already_declared is False:
                    env.create_mutuable_binding(arg_name, configurable_bindings)
                env.set_mutable_binding(arg_name, v, False)

        # 5.
        func_declarations = code.functions()
        for fn in func_declarations:
            fo = None
            func_already_declared = env.has_binding(fn)
            if func_already_declared is False:
                env.create_mutuable_binding(fn, configurable_bindings)
            else:
                pass  # see 10.5 5.e
            env.set_mutable_binding(fn, fo, False)

        arguments_already_declared = env.has_binding(u'arguments')
        # 7.
        if code.is_function_code() and arguments_already_declared is False:
            from js.jsobj import W_Arguments
            # TODO get calling W_Function
            func = self._w_func_
            arguments = self._argument_values_
            names = self._formal_parameters_
            args_obj = W_Arguments(func, names, arguments, env, strict)

            if strict is True:
                env.create_immutable_bining(u'arguments')
                env.initialize_immutable_binding(u'arguments', args_obj)
            else:
                env.create_mutuable_binding(u'arguments', False)  # TODO not sure if mutable binding is deletable
                env.set_mutable_binding(u'arguments', args_obj, False)

        # 8.
        var_declarations = code.variables()
        for dn in var_declarations:
            var_already_declared = env.has_binding(dn)
            if var_already_declared is False:
                env.create_mutuable_binding(dn, configurable_bindings)
                env.set_mutable_binding(dn, w_Undefined, False)

    def _get_refs(self, index):
        assert index <= len(self._refs_)
        return self._refs_[index]

    def _set_refs(self, index, value):
        assert index <= len(self._refs_)
        self._refs_[index] = value

    def get_ref(self, symbol, index=-1):
        ## TODO pre-bind symbols, work with idndex, does not work, see test_foo19
        if index == -1:
            lex_env = self.lexical_environment()
            ref = lex_env.get_identifier_reference(symbol)
            return ref

        if self._refs_resizable_ is True and index >= len(self._refs_):
            self._refs_ += ([None] * (1 + index - len(self._refs_)))

        if self._get_refs(index) is None:
            lex_env = self.lexical_environment()
            ref = lex_env.get_identifier_reference(symbol)
            if ref.is_unresolvable_reference() is True:
                return ref
            self._set_refs(index, ref)

        return self._get_refs(index)

    def forget_ref(self, symbol, index):
        self._set_refs(index, None)


class GlobalExecutionContext(ExecutionContext):
    def __init__(self, code, global_object, strict=False):
        stack_size = code.estimated_stack_size()

        ExecutionContext.__init__(self, stack_size)

        self._code_ = code
        self._strict_ = strict

        from js.lexical_environment import ObjectEnvironment
        localEnv = ObjectEnvironment(global_object)
        self._lexical_environment_ = localEnv
        self._variable_environment_ = localEnv
        self._this_binding_ = global_object

        self.declaration_binding_initialization()


class EvalExecutionContext(ExecutionContext):
    def __init__(self, code, calling_context=None):
        stack_size = code.estimated_stack_size()

        ExecutionContext.__init__(self, stack_size)
        self._code_ = code
        self._strict_ = code.strict

        if not calling_context:
            raise NotImplementedError()
        else:
            self._this_binding_ = calling_context.this_binding()
            self._variable_environment_ = calling_context.variable_environment()
            self._lexical_environment_ = calling_context.lexical_environment()
        if self._strict_:
            from js.lexical_environment import DeclarativeEnvironment
            strict_var_env = DeclarativeEnvironment(self._lexical_environment_)
            self._variable_environment_ = strict_var_env
            self._lexical_environment_ = strict_var_env

        self.declaration_binding_initialization()


class FunctionExecutionContext(ExecutionContext):
    _immutable_fields_ = ['_scope_', '_calling_context_']
    _refs_resizable_ = False
    def __init__(self, code, formal_parameters=[], argv=[], this=w_Undefined, strict=False, scope=None, w_func=None):
        from js.jsobj import isnull_or_undefined, W_BasicObject
        from js.object_space import object_space

        stack_size = code.estimated_stack_size()
        env_size = code.env_size() + 1  # neet do add one for the arguments object

        ExecutionContext.__init__(self, stack_size, env_size)

        self._code_ = code
        self._formal_parameters_ = formal_parameters
        self._argument_values_ = argv
        self._strict_ = strict
        self._scope_ = scope
        self._w_func_ = w_func
        self._calling_context_ = None

        from js.lexical_environment import DeclarativeEnvironment
        localEnv = DeclarativeEnvironment(scope, env_size, False)
        self._lexical_environment_ = localEnv
        self._variable_environment_ = localEnv

        if strict:
            self._this_binding_ = this
        else:
            if this is None or isnull_or_undefined(this):
                self._this_binding_ = object_space.global_object
            else:
                assert isinstance(this, W_BasicObject)

                if this.klass() is not 'Object':
                    self._this_binding_ = this.ToObject()
                else:
                    self._this_binding_ = this

        self.declaration_binding_initialization()

    def argv(self):
        return self._argument_values_


class SubExecutionContext(ExecutionContext):
    def __init__(self, parent):
        ExecutionContext.__init__(self)
        self._parent_context_ = parent

    def stack_append(self, value):
        self._parent_context_.stack_append(value)

    def stack_pop(self):
        return self._parent_context_.stack_pop()

    def stack_top(self):
        return self._parent_context_.stack_top()

    def stack_pop_n(self, n):
        return self._parent_context_.stack_pop_n(n)

    def this_binding(self):
        return self._parent_context_.this_binding()


class WithExecutionContext(SubExecutionContext):
    def __init__(self, code, expr_obj, parent_context):
        SubExecutionContext.__init__(self, parent_context)
        self._code_ = code
        self._strict_ = code.strict
        self._expr_obj_ = expr_obj

        from js.lexical_environment import ObjectEnvironment
        parent_environment = parent_context.lexical_environment()
        local_env = ObjectEnvironment(expr_obj, outer_environment=parent_environment)
        local_env.environment_record.provide_this = True

        self._lexical_environment_ = local_env
        self._variable_environment_ = local_env

        self.declaration_binding_initialization()


class CatchExecutionContext(ExecutionContext):
    def __init__(self, code, catchparam, exception_value, parent_context):
        self._code_ = code
        self._strict_ = code.strict
        self._parent_context_ = parent_context

        stack_size = code.estimated_stack_size()
        env_size = code.env_size() + 1  # neet do add one for the arguments object

        ExecutionContext.__init__(self, stack_size, env_size)

        parent_env = parent_context.lexical_environment()

        from js.lexical_environment import DeclarativeEnvironment
        local_env = DeclarativeEnvironment(parent_env)
        local_env_rec = local_env.environment_record
        local_env_rec.create_mutuable_binding(catchparam, True)
        local_env_rec.set_mutable_binding(catchparam, exception_value, False)

        self._lexical_environment_ = local_env
        self._variable_environment_ = local_env

        self.declaration_binding_initialization()

    def this_binding(self):
        return self._parent_context_.this_binding()
