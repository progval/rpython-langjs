from js.object_space import _w
from js.interpreter import Interpreter
from js.astbuilder import parse_to_ast


class TestInterpreter(object):
    def test_foo1(self):
        src = u'''
        var a = 40;
        var b = 2;
        a + b;
        '''

        ast = parse_to_ast(src)

        interp = Interpreter()
        res = interp.run_ast(ast)

        assert res == _w(42)

    def test_foo2(self):
        src = '''
        var a = 40;
        var b = 2;
        return a + b;
        '''

        interp = Interpreter()
        res = interp.run_src(src)

        assert res == _w(42)

    def test_foo3(self):
        interp = Interpreter()
        res = interp.run_src('var a = 40;')
        res = interp.run_src('var b = 2;')
        res = interp.run_src('a + b;')

        assert res == _w(42)

    def test_foo4(self):
        interp = Interpreter()
        res = interp.run_src('40 + 2;')

        assert res == _w(42)
