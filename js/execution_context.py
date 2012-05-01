from js.jsobj import w_Undefined

_global_object_ = None

def get_global_object():
    return GlobalExecutionContext.global_object

class ExecutionContext(object):
    def __init__(self):
        self._stack_ = []
        self._lexical_environment_ = None
        self._variable_environment_ = None
        self._this_binding_ = None

    def declaration_binding_initialization(self, env, code, arguments = []):
        configurable_bindings = code.configurable_bindings

        n = 0
        arg_count = len(arguments)

        names = code.params()
        for arg_name in names:
            n += 1
            if n > arg_count:
                v = w_Undefined
            else:
                v = arguments[n-1]
            arg_already_declared = env.has_binding(arg_name)
            if arg_already_declared is False:
                env.create_mutuable_binding(arg_name, configurable_bindings)
            env.set_mutable_binding(arg_name, v)

        func_declarations = code.functions()
        for fn in func_declarations:
            fo = None
            func_already_declared = env.has_binding(fn)
            if func_already_declared is False:
                env.create_mutuable_binding(fn, configurable_bindings)
            else:
                pass #see 10.5 5.e
            env.set_mutable_binding(fn, fo)

        var_declarations = code.variables()
        for dn in var_declarations:
            var_already_declared = env.has_binding(dn)
            if var_already_declared == False:
                env.create_mutuable_binding(dn, configurable_bindings)
                env.set_mutable_binding(dn, w_Undefined)

    def stack_append(self, value):
        self._stack_.append(value)

    def stack_pop(self):
        return self._stack_.pop()

    def stack_top(self):
        return self._stack_[-1]

    def stack_pop_n(self, n):
        if n < 1:
            return []

        i = -1 * n
        r = self._stack_[i:]
        s = self._stack_[:i]
        self._stack_  = s
        return r

    def run(self):
        raise NotImplementedError(self.__class__)

    def get_value(self, index):
        raise NotImplementedError(self.__class__)

    def set_value(self, index, value):
        raise NotImplementedError(self.__class__)

    def this_binding(self):
        return self._this_binding_

    def variable_environment(self):
        return self._variable_environment_

    def lexical_environment(self):
        return self._lexical_environment_

class GlobalExecutionContext(ExecutionContext):
    global_object = None
    def __init__(self, code, global_object):
        ExecutionContext.__init__(self)
        self.code = code

        from js.lexical_environment import ObjectEnvironment
        localEnv = ObjectEnvironment(global_object)
        self._lexical_environment_ = localEnv
        self._variable_environment_ = localEnv
        GlobalExecutionContext.global_object = global_object
        self._this_binding_ = global_object

        self.declaration_binding_initialization(self._variable_environment_.environment_record, self.code)

    def run(self):
        return self.code.run(self)

    def _symbol_for_index(self, index):
        sym = self.code.symbol_for_index(index)
        assert sym is not None
        return sym

    def get_ref(self, index):
        symbol = self._symbol_for_index(index)
        lex_env = self.lexical_environment()
        ref = lex_env.get_identifier_reference(symbol)
        return ref

    #def get_value(self, index):
        #env = self.variable_environment()
        #env_record = env.environment_record
        #identifier = self._symbol_for_index(index)
        #value = env_record.get_binding_value(identifier)
        #return value

    #def set_value(self, index, value):
        #env = self.variable_environment()
        #env_record = env.environment_record
        #identifier = self._symbol_for_index(index)
        #env_record.set_mutable_binding(identifier, value)

class EvalExecutionContext(ExecutionContext):
    pass

class FunctionExecutionContext(ExecutionContext):
    def __init__(self, function, this, argument_values, scope = None):
        ExecutionContext.__init__(self)
        self.function = function
        self.arguments = argument_values

        from js.lexical_environment import DeclarativeEnvironment
        localEnv = DeclarativeEnvironment(scope)
        self._lexical_environment_ = localEnv
        self._variable_environment_ = localEnv

        self._this_binding_ = this

        self.symbol_slots = {}
        self.declaration_binding_initialization(self._variable_environment_.environment_record, self.function, self.arguments)

    def run(self):
        self._bind_symbols()
        return self.function.run(self)

    def _bind_symbols(self):
        lex_env = self.variable_environment()
        for symbol in self.function.symbols():
            idx = self._index_for_symbol(symbol)
            ref = lex_env.get_identifier_reference(symbol)
            self.symbol_slots[idx] = ref

    def _index_for_symbol(self, symbol):
        return self.function.index_for_symbol(symbol)

    def get_ref(self, index):
        ref = self.symbol_slots[index]
        return ref

    #def get_value(self, index):
        #ref = self.get_ref(index)
        #env_record = ref.base_value
        #identifier = ref.referenced
        #value = env_record.get_binding_value(identifier)
        #return value

    #def set_value(self, index, value):
        #ref = self.symbol_slots[index]
        #env_record = ref.base_value
        #identifier = ref.referenced
        #env_record.set_mutable_binding(identifier, value)
