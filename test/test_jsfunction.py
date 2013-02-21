from js.object_space import _w
from js.jscode import JsCode
from js.execution_context import ExecutionContext, FunctionExecutionContext, GlobalExecutionContext, EvalExecutionContext
from js.functions import JsFunction, JsExecutableCode, JsNativeFunction, JsGlobalCode, JsEvalCode
from js.lexical_environment import DeclarativeEnvironment
from js.astbuilder import parse_to_ast, SymbolMap
from js.jscode import ast_to_bytecode
from js.jsobj import W_BasicObject


class FakeInterpreter(object):
    from js.interpreter import InterpreterConfig
    config = InterpreterConfig()

from js.object_space import object_space
object_space.interpreter = FakeInterpreter()

from js.jsobj import W_GlobalObject
object_space.global_object = W_GlobalObject()


class TestJsFunctionAndStuff(object):
    def test_foo1(self):
        code = JsCode()
        code.emit('LOAD_INTCONSTANT', 1)
        code.emit('LOAD_INTCONSTANT', 1)
        code.emit('ADD')
        code.emit('RETURN')

        f = JsExecutableCode(code)
        ctx = ExecutionContext(stack_size=f.estimated_stack_size())
        res = f.run(ctx)
        assert res.value == _w(2)

    def test_foo2(self):
        code = JsCode()
        code.emit('LOAD_INTCONSTANT', 1)
        code.emit('LOAD_INTCONSTANT', 1)
        code.emit('ADD')
        code.emit('RETURN')

        f = JsFunction(u'foo', code)
        ctx = FunctionExecutionContext(f)
        res = f.run(ctx)

        assert res.value == _w(2)

    def test_foo3(self):
        symbol_map = SymbolMap()
        var_idx = symbol_map.add_parameter(u'a')

        code = JsCode(symbol_map)
        code.emit('LOAD_VARIABLE', var_idx, u'a')
        code.emit('RETURN')

        f = JsFunction(u'foo', code)
        ctx = FunctionExecutionContext(f, argv=[_w(42)])

        res = f.run(ctx)
        assert res.value == _w(42)

    def test_foo4(self):
        symbol_map = SymbolMap()
        var_idx_a = symbol_map.add_variable(u'a')
        var_idx_b = symbol_map.add_parameter(u'b')

        code = JsCode(symbol_map)
        code.emit('LOAD_VARIABLE', var_idx_a, u'a')
        code.emit('LOAD_VARIABLE', var_idx_b, u'b')
        code.emit('ADD')
        code.emit('RETURN')

        f = JsFunction(u'foo', code)

        ctx = FunctionExecutionContext(f, formal_parameters=[u'b'], argv=[_w(21)])

        lex = ctx.variable_environment()
        env_rec = lex.environment_record
        env_rec.set_mutable_binding(u'a', _w(21), False)

        res = f.run(ctx)
        assert res.value == _w(42)

    def test_foo5(self):
        symbol_map = SymbolMap()
        var_idx_a = symbol_map.add_variable(u'a')
        var_idx_b = symbol_map.add_parameter(u'b')

        code = JsCode(symbol_map)
        code.emit('LOAD_VARIABLE', var_idx_a, u'a')
        code.emit('LOAD_VARIABLE', var_idx_b, u'b')
        code.emit('ADD')
        code.emit('STORE', var_idx_a, u'a')
        code.emit('RETURN')

        f = JsFunction(u'foo', code)
        ctx = FunctionExecutionContext(f, formal_parameters=[u'b'], argv=[_w(21)])

        lex_env = ctx.variable_environment()
        env_rec = lex_env.environment_record
        env_rec.set_mutable_binding(u'a', _w(21), False)

        res = f.run(ctx)

        assert env_rec.get_binding_value(u'a') == _w(42)
        assert res.value == _w(42)

    def test_foo6(self):
        symbol_map = SymbolMap()
        var_idx_a = symbol_map.add_variable(u'a')
        var_idx_b = symbol_map.add_symbol(u'b')

        code = JsCode(symbol_map)
        code.emit('LOAD_VARIABLE', var_idx_a, u'a')
        code.emit('LOAD_VARIABLE', var_idx_b, u'b')
        code.emit('ADD')
        code.emit('STORE', var_idx_a, u'a')
        code.emit('RETURN')

        outer_env = DeclarativeEnvironment()
        outer_env_rec = outer_env.environment_record

        f = JsFunction(u'foo', code)

        ctx = FunctionExecutionContext(f, scope=outer_env)

        lex_env = ctx.variable_environment()
        env_rec = lex_env.environment_record

        env_rec.set_mutable_binding(u'a', _w(21), False)

        outer_env_rec.create_mutuable_binding(u'b', True)
        outer_env_rec.set_mutable_binding(u'b', _w(21), False)

        res = f.run(ctx)

        assert env_rec.get_binding_value(u'a') == _w(42)
        assert outer_env_rec.get_binding_value(u'b') == _w(21)
        assert res.value == _w(42)

    def test_foo7(self):
        symbol_map = SymbolMap()
        var_idx_a = symbol_map.add_variable(u'a')
        var_idx_b = symbol_map.add_symbol(u'b')

        code = JsCode(symbol_map)
        code.emit('LOAD_VARIABLE', var_idx_a, u'a')
        code.emit('LOAD_VARIABLE', var_idx_b, u'b')
        code.emit('ADD')
        code.emit('STORE', var_idx_b, u'b')
        code.emit('RETURN')

        outer_env = DeclarativeEnvironment()
        outer_env_rec = outer_env.environment_record

        f = JsFunction(u'foo', code)

        ctx = FunctionExecutionContext(f, scope=outer_env)

        lex_env = ctx.variable_environment()
        env_rec = lex_env.environment_record

        env_rec.set_mutable_binding(u'a', _w(21), False)

        outer_env_rec.create_mutuable_binding(u'b', True)
        outer_env_rec.set_mutable_binding(u'b', _w(21), False)

        res = f.run(ctx)

        assert env_rec.get_binding_value(u'a') == _w(21)
        assert outer_env_rec.get_binding_value(u'b') == _w(42)
        assert res.value == _w(42)

    def test_foo8(self):
        symbol_map = SymbolMap()
        var_idx_a = symbol_map.add_variable(u'a')
        var_idx_b = symbol_map.add_variable(u'b')
        var_idx_c = symbol_map.add_variable(u'c')

        code = JsCode(symbol_map)
        code.emit('LOAD_INTCONSTANT', 21)
        code.emit('STORE', var_idx_a, u'a')
        code.emit('POP')
        code.emit('LOAD_INTCONSTANT', 21)
        code.emit('STORE', var_idx_b, u'b')
        code.emit('POP')
        code.emit('LOAD_VARIABLE', var_idx_a, u'a')
        code.emit('LOAD_VARIABLE', var_idx_b, u'b')
        code.emit('ADD')
        code.emit('STORE', var_idx_c, u'c')
        code.emit('RETURN')

        f = JsGlobalCode(code)

        w_global = W_BasicObject()

        ctx = GlobalExecutionContext(f, w_global)
        res = f.run(ctx)

        lex_env = ctx.variable_environment()
        env_rec = lex_env.environment_record

        assert env_rec.get_binding_value(u'a') == _w(21)
        assert env_rec.get_binding_value(u'b') == _w(21)
        assert env_rec.get_binding_value(u'c') == _w(42)
        assert res.value == _w(42)

    def test_foo9(self):
        src = u'''
        var a = 21;
        var b = 21;
        var c = a + b;
        return c;
        '''

        ast = parse_to_ast(src)
        symbol_map = ast.symbol_map
        code = ast_to_bytecode(ast, symbol_map)

        f = JsGlobalCode(code)

        w_global = W_BasicObject()
        ctx = GlobalExecutionContext(f, w_global)
        res = f.run(ctx)

        lex_env = ctx.variable_environment()
        env_rec = lex_env.environment_record

        assert env_rec.get_binding_value(u'a') == _w(21)
        assert env_rec.get_binding_value(u'b') == _w(21)
        assert env_rec.get_binding_value(u'c') == _w(42)
        assert res.value == _w(42)

    def test_foo10(self):
        src = u'''
        function f() {
            return 42;
        }
        var a = f();
        return a;
        '''

        ast = parse_to_ast(src)
        symbol_map = ast.symbol_map
        code = ast_to_bytecode(ast, symbol_map)

        f = JsGlobalCode(code)
        w_global = W_BasicObject()

        ctx = GlobalExecutionContext(f, w_global)
        res = f.run(ctx)

        lex_env = ctx.variable_environment()
        env_rec = lex_env.environment_record

        assert env_rec.get_binding_value(u'a') == _w(42)
        assert res.value == _w(42)

    def test_foo11(self):
        src = u'''
        function f(b) {
            var c = 21;
            return b + c;
        }
        var a = f(21);
        return a;
        '''

        ast = parse_to_ast(src)
        symbol_map = ast.symbol_map
        code = ast_to_bytecode(ast, symbol_map)

        f = JsGlobalCode(code)

        w_global = W_BasicObject()
        ctx = GlobalExecutionContext(f, w_global)
        res = f.run(ctx)

        lex_env = ctx.variable_environment()
        env_rec = lex_env.environment_record

        assert env_rec.get_binding_value(u'a') == _w(42)
        assert env_rec.has_binding(u'b') is False
        assert env_rec.has_binding(u'c') is False
        assert res.value == _w(42)

    def test_foo12(self):
        src = u'''
        function fib(n) {
            if(n<2) {
                return n;
            } else {
                return fib(n-1) + fib(n-2);
            }
        }
        return fib(10);
        '''

        ast = parse_to_ast(src)
        symbol_map = ast.symbol_map
        code = ast_to_bytecode(ast, symbol_map)

        f = JsGlobalCode(code)

        w_global = W_BasicObject()
        ctx = GlobalExecutionContext(f, w_global)
        res = f.run(ctx)

        assert res.value == _w(55)

    def test_foo13(self):
        def f(this, args):
            a = args[0].ToInteger()
            return _w(a + 1)

        func = JsNativeFunction(f)
        ctx = FunctionExecutionContext(func, argv=[_w(41)])
        res = func.run(ctx)

        assert res.value == _w(42)

    def test_foo14(self):
        def f(this, args):
            a = args[0].ToInteger()
            return _w(a + 1)

        func = JsNativeFunction(f)

        from js.jsobj import W__Function
        w_func = W__Function(func)

        w_global = W_BasicObject()
        w_global.put(u'f', w_func)

        src = u'''
        return f(41);
        '''

        ast = parse_to_ast(src)
        symbol_map = ast.symbol_map
        code = ast_to_bytecode(ast, symbol_map)

        c = JsGlobalCode(code)
        ctx = GlobalExecutionContext(c, w_global)
        res = c.run(ctx)

        assert res.value == _w(42)

    def test_foo15(self):
        code = JsCode()
        code.emit('LOAD_INTCONSTANT', 1)
        code.emit('LOAD_INTCONSTANT', 1)
        code.emit('ADD')

        f = JsExecutableCode(code)

        ctx = ExecutionContext(stack_size=f.estimated_stack_size())
        res = f.run(ctx)
        assert res.value == _w(2)

    def test_foo16(self):
        src = u'''
        a = 1;
        b = 41;
        a + b;
        '''
        res = self.run_src(src)
        assert res == _w(42)

    def test_foo17(self):
        src = u'''
        function f() {
            a = 42;
        }
        f();
        a;
        '''

        res = self.run_src(src)
        assert res == _w(42)

    def test_foo18(self):
        src = u'''
        a = 42;
        this.a;
        '''

        res = self.run_src(src)
        assert res == _w(42)

    def test_foo19(self):
        src = u'''
        function x() { d=2; return d;}; x();
        '''

        res = self.run_src(src)
        assert res == _w(2)

    def test_foo20(self):
        src = u'''
        ;
        '''

        ast = parse_to_ast(src)
        symbol_map = ast.symbol_map
        code = ast_to_bytecode(ast, symbol_map)

        global_code = JsGlobalCode(code)
        global_object = W_BasicObject()
        global_ctx = GlobalExecutionContext(global_code, global_object)

        src = u'''
        a = 1;
        '''

        ast = parse_to_ast(src)
        symbol_map = ast.symbol_map
        code = ast_to_bytecode(ast, symbol_map)

        f = JsEvalCode(code)

        ctx = EvalExecutionContext(f, calling_context=global_ctx)
        res = f.run(ctx)

        assert res.value == _w(1)

    def run_src(self, src):
        ast = parse_to_ast(src)
        symbol_map = ast.symbol_map
        code = ast_to_bytecode(ast, symbol_map)

        c = JsGlobalCode(code)

        w_global = W_BasicObject()
        object_space.global_object = w_global
        ctx = GlobalExecutionContext(c, w_global)
        res = c.run(ctx)
        return res.value
