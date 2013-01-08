from pypy import conftest


class o:
    view = False
    viewloops = True
conftest.option = o

from pypy.jit.metainterp.test.support import LLJitMixin

from js import interpreter


class TestJtTrace(LLJitMixin):
    def test_simple_loop(self):
        code = """
        var i = 0;
        while(i < 100) {
            i += 1;
        }
        return i;
        """
        jsint = interpreter.Interpreter()

        def interp_w():
            code_val = jsint.run_src(code)
            return code_val.ToNumber()
        assert self.meta_interp(interp_w, [], listcomp=True, backendopt=True, listops=True) == 100

    def test_loop_in_func(self):
        code = """
        function f() {
            var i = 0;
            while(i < 100) {
                i += 1;
            }
            return i;
        }
        return f();
        """
        jsint = interpreter.Interpreter()

        def interp_w():
            code_val = jsint.run_src(code)
            return code_val.ToNumber()
        assert self.meta_interp(interp_w, [], listcomp=True, backendopt=True, listops=True) == 100

    def test_prop_loop_in_func(self):
        code = """
        function f() {
            var x = {i: 0};
            while(x.i < 100) {
                x.i += 1;
            }
            return x.i;
        }
        return f();
        """
        jsint = interpreter.Interpreter()

        def interp_w():
            code_val = jsint.run_src(code)
            return code_val.ToNumber()
        assert self.meta_interp(interp_w, [], listcomp=True, backendopt=True, listops=True) == 100

    def test_object_alloc_loop_in_func_loop(self):
        code = """
        function f() {
            var x = {i: 0};
            while(x.i < 100) {
                x = {i: x.i + 1};
            }
            return x.i;
        }
        return f();
        """
        jsint = interpreter.Interpreter()

        def interp_w():
            code_val = jsint.run_src(code)
            return code_val.ToNumber()
        assert self.meta_interp(interp_w, [], listcomp=True, backendopt=True, listops=True) == 100

    def test_func_call_in_loop(self):
        code = """
        var i = 0;
        function f(a) {
            return a + 1;
        }
        while(i < 100) {
            i = f(i);
        }
        return i;
        """
        jsint = interpreter.Interpreter()

        def interp_w():
            code_val = jsint.run_src(code)
            return code_val.ToNumber()
        assert self.meta_interp(interp_w, [], listcomp=True, backendopt=True, listops=True) == 100

    def test_loop_not_escapeing(self):
        code = """
        function f() {
            var a = 0;
            for (var i = 0; i< 100; i++) {
                a = 0;
            }
            return a;
        }
        f();
        """
        jsint = interpreter.Interpreter()

        def interp_w():
            code_val = jsint.run_src(code)
            return code_val.ToNumber()
        assert self.meta_interp(interp_w, [], listcomp=True, backendopt=True, listops=True) == 100

    def test_loop_little_escapeing(self):
        code = """
        function f() {
            var a = 0;
            for (var i = 0; i< 100; i++) {
                a = i;
            }
            return a;
        }
        f();
        """
        jsint = interpreter.Interpreter()

        def interp_w():
            code_val = jsint.run_src(code)
            return code_val.ToNumber()
        assert self.meta_interp(interp_w, [], listcomp=True, backendopt=True, listops=True) == 100

    def test_bitwise_and(self):
        code = """
        function f() {
            bitwiseAndValue = 4294967296;
            for (var i = 0; i < 600000; i++) {
                    bitwiseAndValue = bitwiseAndValue & i;
            }
        }
        f();
        1;
        """
        jsint = interpreter.Interpreter()

        def interp_w():
            code_val = jsint.run_src(code)
            return code_val.ToNumber()
        assert self.meta_interp(interp_w, [], listcomp=True, backendopt=True, listops=True) == 1
