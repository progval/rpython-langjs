import py
#from js.jscode import _JsFunction
from js.jsobj import _w
from js.jscode import JsCode
from js.execution_context import ExecutionContext, FunctionExecutionContext, GlobalExecutionContext
from js.functions import JsFunction, JsExecutableCode, JsNativeFunction, JsGlobalCode
from js.lexical_environment import DeclarativeEnvironment
from js.astbuilder import parse_to_ast, SymbolMap
from js.jscode import ast_to_bytecode
from js.jsobj import W_BasicObject

class TestJsFunctionAndStuff(object):
    def test_foo1(self):
        code = JsCode()
        code.emit('LOAD_INTCONSTANT', 1)
        code.emit('LOAD_INTCONSTANT', 1)
        code.emit('ADD')
        code.emit('RETURN')

        f = JsExecutableCode(code)
        ctx = ExecutionContext()
        res = f.run(ctx)
        assert res == _w(2)

    def test_foo2(self):
        code = JsCode()
        code.emit('LOAD_INTCONSTANT', 1)
        code.emit('LOAD_INTCONSTANT', 1)
        code.emit('ADD')
        code.emit('RETURN')

        f = JsFunction('foo', code)
        ctx = FunctionExecutionContext(f, None, [])

        res = ctx.run()
        assert res == _w(2)


    def test_foo3(self):
        symbol_map = SymbolMap()
        var_idx = symbol_map.add_variable('a')

        code = JsCode(symbol_map)
        code.emit('LOAD_VARIABLE', var_idx)
        code.emit('RETURN')

        f = JsFunction('foo', code)
        ctx = FunctionExecutionContext(f, None, [])

        lex_env = ctx.variable_environment()
        env_rec = lex_env.environment_record
        env_rec.set_mutable_binding('a', _w(42))

        res = ctx.run()
        assert res == _w(42)

    def test_foo4(self):
        symbol_map = SymbolMap()
        var_idx_a = symbol_map.add_variable('a')
        var_idx_b = symbol_map.add_parameter('b')

        code = JsCode(symbol_map)
        code.emit('LOAD_VARIABLE', var_idx_a)
        code.emit('LOAD_VARIABLE', var_idx_b)
        code.emit('ADD')
        code.emit('RETURN')

        f = JsFunction('foo', code)
        ctx = FunctionExecutionContext(f, None, [_w(21)])

        lex_env = ctx.variable_environment()
        env_rec = lex_env.environment_record
        env_rec.set_mutable_binding('a', _w(21))

        res = ctx.run()
        assert res == _w(42)

    def test_foo5(self):
        symbol_map = SymbolMap()
        var_idx_a = symbol_map.add_variable('a')
        var_idx_b = symbol_map.add_parameter('b')

        code = JsCode(symbol_map)
        code.emit('LOAD_VARIABLE', var_idx_a)
        code.emit('LOAD_VARIABLE', var_idx_b)
        code.emit('ADD')
        code.emit('STORE', var_idx_a)
        code.emit('RETURN')

        f = JsFunction('foo', code)
        ctx = FunctionExecutionContext(f, None, [_w(21)])

        lex_env = ctx.variable_environment()
        env_rec = lex_env.environment_record
        env_rec.set_mutable_binding('a', _w(21))

        res = ctx.run()

        assert env_rec.get_binding_value('a') == _w(42)
        assert res == _w(42)

    def test_foo6(self):
        symbol_map = SymbolMap()
        var_idx_a = symbol_map.add_variable('a')
        var_idx_b = symbol_map.add_symbol('b')

        code = JsCode(symbol_map)
        code.emit('LOAD_VARIABLE', var_idx_a)
        code.emit('LOAD_VARIABLE', var_idx_b)
        code.emit('ADD')
        code.emit('STORE', var_idx_a)
        code.emit('RETURN')

        outer_env = DeclarativeEnvironment()
        outer_env_rec = outer_env.environment_record

        f = JsFunction('foo', code)

        ctx = FunctionExecutionContext(f, None, [], outer_env)

        lex_env = ctx.variable_environment()
        env_rec = lex_env.environment_record

        env_rec.set_mutable_binding('a', _w(21))

        outer_env_rec.create_mutuable_binding('b', True)
        outer_env_rec.set_mutable_binding('b', _w(21))

        res = ctx.run()

        assert env_rec.get_binding_value('a') == _w(42)
        assert outer_env_rec.get_binding_value('b') == _w(21)
        assert res == _w(42)

    def test_foo7(self):
        symbol_map = SymbolMap()
        var_idx_a = symbol_map.add_variable('a')
        var_idx_b = symbol_map.add_symbol('b')

        code = JsCode(symbol_map)
        code.emit('LOAD_VARIABLE', var_idx_a)
        code.emit('LOAD_VARIABLE', var_idx_b)
        code.emit('ADD')
        code.emit('STORE', var_idx_b)
        code.emit('RETURN')

        outer_env = DeclarativeEnvironment()
        outer_env_rec = outer_env.environment_record

        f = JsFunction('foo', code)

        ctx = FunctionExecutionContext(f, None, [], outer_env)

        lex_env = ctx.variable_environment()
        env_rec = lex_env.environment_record

        env_rec.set_mutable_binding('a', _w(21))

        outer_env_rec.create_mutuable_binding('b', True)
        outer_env_rec.set_mutable_binding('b', _w(21))

        res = ctx.run()

        assert env_rec.get_binding_value('a') == _w(21)
        assert outer_env_rec.get_binding_value('b') == _w(42)
        assert res == _w(42)

    def test_foo8(self):
        symbol_map = SymbolMap()
        var_idx_a = symbol_map.add_variable('a')
        var_idx_b = symbol_map.add_variable('b')
        var_idx_c = symbol_map.add_variable('c')

        code = JsCode(symbol_map)
        code.emit('LOAD_INTCONSTANT', 21)
        code.emit('STORE', var_idx_a)
        code.emit('POP')
        code.emit('LOAD_INTCONSTANT', 21)
        code.emit('STORE', var_idx_b)
        code.emit('POP')
        code.emit('LOAD_VARIABLE', var_idx_a)
        code.emit('LOAD_VARIABLE', var_idx_b)
        code.emit('ADD')
        code.emit('STORE', var_idx_c)
        code.emit('RETURN')

        f = JsGlobalCode(code)

        w_global = W_BasicObject()

        ctx = GlobalExecutionContext(f, w_global)
        res = ctx.run()

        lex_env = ctx.variable_environment()
        env_rec = lex_env.environment_record

        assert env_rec.get_binding_value('a') == _w(21)
        assert env_rec.get_binding_value('b') == _w(21)
        assert env_rec.get_binding_value('c') == _w(42)
        assert res == _w(42)

    def test_foo9(self):
        src = '''
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
        res = ctx.run()

        lex_env = ctx.variable_environment()
        env_rec = lex_env.environment_record

        assert env_rec.get_binding_value('a') == _w(21)
        assert env_rec.get_binding_value('b') == _w(21)
        assert env_rec.get_binding_value('c') == _w(42)
        assert res == _w(42)

    def test_foo10(self):
        src = '''
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

        ctx = GlobalExecutionContext(f)
        res = ctx.run()

        lex_env = ctx.variable_environment()
        env_rec = lex_env.environment_record

        assert env_rec.get_binding_value('a') == _w(42)
        assert res == _w(42)

    def test_foo10(self):
        src = '''
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
        res = ctx.run()

        lex_env = ctx.variable_environment()
        env_rec = lex_env.environment_record

        assert env_rec.get_binding_value('a') == _w(42)
        assert env_rec.has_binding('b') is False
        assert env_rec.has_binding('c') is False
        assert res == _w(42)

    def test_foo11(self):
        src = '''
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
        res = ctx.run()

        assert res == _w(55)

    def test_foo12(self):
        def f(args, this):
            a = args[0].ToInteger()
            return _w(a + 1)

        func = JsNativeFunction(f)
        ctx = FunctionExecutionContext(func, None, [_w(41)])
        res = ctx.run()

        assert res == _w(42)

    def test_foo13(self):
        def f(args, this):
            a = args[0].ToInteger()
            return _w(a + 1)

        func = JsNativeFunction(f)

        from js.jsobj import W__Function
        w_func = W__Function(func, None)

        w_global = W_BasicObject()
        w_global.put('f', w_func)

        src = '''
        return f(41);
        '''

        ast = parse_to_ast(src)
        symbol_map = ast.symbol_map
        code = ast_to_bytecode(ast, symbol_map)

        c = JsGlobalCode(code)
        ctx = GlobalExecutionContext(c, w_global)
        res = ctx.run()

        assert res == _w(42)

    def test_foo14(self):
        code = JsCode()
        code.emit('LOAD_INTCONSTANT', 1)
        code.emit('LOAD_INTCONSTANT', 1)
        code.emit('ADD')

        f = JsExecutableCode(code)
        ctx = ExecutionContext()
        res = f.run(ctx)
        assert res == _w(2)

    def test_foo15(self):
        src = '''
        a = 1;
        b = 41;
        a + b;
        '''
        res = self.run_src(src)
        assert res == _w(42)

    def test_foo16(self):
        src = '''
        function f() {
            a = 42;
        }
        f();
        a;
        '''

        res = self.run_src(src)
        assert res == _w(42)

    def test_foo17(self):
        src = '''
        a = 42;
        this.a;
        '''

        res = self.run_src(src)
        assert res == _w(42)


    def run_src(self, src):
        ast = parse_to_ast(src)
        symbol_map = ast.symbol_map
        code = ast_to_bytecode(ast, symbol_map)

        c = JsGlobalCode(code)

        w_global = W_BasicObject()
        ctx = GlobalExecutionContext(c, w_global)
        res = ctx.run()
        return res
