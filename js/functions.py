from js.object_space import _w


class JsBaseFunction(object):
    _settled_ = True
    eval_code = False
    function_code = False
    configurable_bindings = False
    strict = False

    def run(self, ctx):
        raise NotImplementedError

    def estimated_stack_size(self):
        return 2

    def to_string(self):
        return u'function() {}'

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

    def env_size(self):
        return 0


class JsNativeFunction(JsBaseFunction):
    _immutable_fields_ = ['_name_', '_function_']

    def __init__(self, function, name=u''):
        assert isinstance(name, unicode)
        self._name_ = name
        self._function_ = function

    def name(self):
        return self._name_

    def run(self, ctx):
        from js.completion import ReturnCompletion

        args = ctx.argv()
        this = ctx.this_binding()
        assert isinstance(self, JsNativeFunction)
        res = self._function_(this, args)
        w_res = _w(res)
        compl = ReturnCompletion(value=w_res)
        return compl

    def to_string(self):
        name = self.name()
        if name is not None:
            return u'function %s() { [native code] }' % (name, )
        else:
            return u'function () { [native code] }'


class JsIntimateFunction(JsNativeFunction):
    _immutable_fields_ = ['_name_', '_intimate_function_']

    def __init__(self, function, name=u''):
        assert isinstance(name, unicode)
        self._name_ = name
        self._intimate_function_ = function

    def run(self, ctx):
        from js.completion import Completion
        compl = self._intimate_function_(ctx)
        assert isinstance(compl, Completion)
        return compl


class JsExecutableCode(JsBaseFunction):
    _immutable_fields_ = ['_js_code_', '_stack_size_', '_symbol_size_']

    def __init__(self, js_code):
        from js.jscode import JsCode
        assert isinstance(js_code, JsCode)
        self._js_code_ = js_code
        self._js_code_.compile()
        self._stack_size_ = js_code.estimated_stack_size()
        self._symbol_size_ = js_code.symbol_size()

    def estimated_stack_size(self):
        return self._stack_size_

    def env_size(self):
        return self._symbol_size_

    def get_js_code(self):
        from js.jscode import JsCode
        assert isinstance(self._js_code_, JsCode)
        return self._js_code_

    def run(self, ctx):
        code = self.get_js_code()
        result = code.run(ctx)
        return result

    def variables(self):
        code = self.get_js_code()
        return code.variables()

    def functions(self):
        # XXX tuning
        code = self.get_js_code()
        functions = code.functions()
        return functions

    def params(self):
        code = self.get_js_code()
        return code.params()

    def name(self):
        return u'_unnamed_'

    def to_string(self):
        name = self.name()
        if name is not None:
            return u'function %s() { }' % (name, )
        else:
            return u'function () { }'


class JsGlobalCode(JsExecutableCode):
    pass


class JsEvalCode(JsExecutableCode):
    def is_eval_code(self):
        return True


class JsFunction(JsExecutableCode):
    _immutable_fields_ = ['_js_code_', '_stack_size_', '_symbol_size_', '_name_']

    def __init__(self, name, js_code):
        assert isinstance(name, unicode)
        JsExecutableCode.__init__(self, js_code)
        js_code._function_name_ = name
        self._name_ = name

    def name(self):
        return self._name_

    def is_function_code(self):
        return True
