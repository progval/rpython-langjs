from rpython import conftest


class o:
    view = False
    viewloops = True
conftest.option = o

from rpython.jit.metainterp.test.support import LLJitMixin
from rpython.rlib import jit

from js import interpreter


class TestJtTrace(LLJitMixin):
    def run(self, code, expected):
        jsint = interpreter.Interpreter()

        def interp_w():
            jit.set_param(None, "inlining", True)
            code_val = jsint.run_src(code)
            return code_val.ToNumber()

        assert self.meta_interp(interp_w, [], listcomp=True, backendopt=True, listops=True) == expected

    def test_simple_loop(self):
        code = """
        var i = 0;
        while(i < 100) {
            i += 1;
        }
        return i;
        """

        self.run(code, 100)

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

        self.run(code, 100)

    def test_float_loop(self):
        code = """
        function f() {
            var i = 0;
            while(i < 100) {
                i += 0.1;
            }
            return i;
        }
        return f();
        """

        self.run(code, 100)

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

        self.run(code, 100)

    def test_simple_object_alloc_loop_in_func_loop(self):
        code = """
        function f() {
            var i = 0;
            while(i < 100) {
                i = {foo: i}.foo + 1;
            }
            return x.i;
        }
        return f();
        """

        self.run(code, 100)

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

        self.run(code, 100)

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

        self.run(code, 100)

    def test_local_func_call_in_loop(self):
        code = """
        (function () {
            var i = 0;
            function f(a) {
                return a + 1;
            }
            while(i < 100) {
                i = f(i);
            }
            return i;
        })();
        """

        self.run(code, 100)

    def test_func_call_multiple_args(self):
        code = """
        (function () {
            var i = 0;
            function f(a, b) {
                return a + b;
            }
            while(i < 100) {
                i = f(i, 1);
            }
            return i;
        })();
        """

        self.run(code, 100)

    def test_double_func_call_in_loop(self):
        code = """
        (function () {
            var i = 0;
            function g(b) {
                return b + 1;
            }
            function f(a) {
                return g(a);
            }
            while(i < 100) {
                i = f(i);
            }
            return i;
        })();
        """

        self.run(code, 100)

    def test_double_nested_func_call_in_loop(self):
        code = """
        (function () {
            var i = 0;
            function f(a) {
                function g(b) {
                    return b + 1;
                }
                return g(a);
            }
            while(i < 100) {
                i = f(i);
            }
            return i;
        })();
        """

        self.run(code, 100)

    def test_double_func_call_in_loop_no_arg(self):
        code = """
        (function () {
            var i = 0;
            function f() {
                function g() {
                    return i + 1;
                }
                return g();
            }
            while(i < 100) {
                i = f();
            }
            return i;
        })();
        """

        self.run(code, 100)

    def test_recursive_func_call(self):
        code = """
        (function () {
            var i = 0;
            function f(a) {
                if (a < 100) {
                    return f(a+1);
                }
                return a;
            }
            return f(0);
        })();
        """

        self.run(code, 100)

    def test_loop_recursive_func_call(self):
        code = """
        (function () {
            function f(a) {
                if (a < 10) {
                    return f(a+1);
                }
                return a;
            }

            var i = 0;
            while(i < 100) {
                i = i + f(i);
            }
            return i;
        })();
        """

        self.run(code, 100)

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
        1;
        """

        self.run(code, 1)

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

        self.run(code, 100)

    def test_bitwise_and(self):
        code = """
        function f() {
            var bitwiseAndValue = 4294967296;
            for (var i = 0; i < 600000; i++) {
                    bitwiseAndValue = bitwiseAndValue & i;
            }
        }
        f();
        1;
        """

        self.run(code, 1)

    def test_str_concat(self):
        code = """
        (function () {
            var i = 0;
            var j = '';
            while(i < 10) {
                i += 1;
                j += 'a';
            }
            return j;
        })();
        """

        self.run(code, 'aaaaaaaaaa')

    def test_array_fill(self):
        code = """
        (function () {
            var i = 0;
            var j = [];
            while(i < 10) {
                j[i] = i;
                i += 1;
            }
            return j;
        })();
        """

        self.run(code, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

    def test_array_fill_2x(self):
        code = """
        (function () {
            var i = 0;
            var j = [];
            while(i < 10) {
                j[i] = null;
                i += 1;
            }
            i = 0;
            while(i < 10) {
                j[i] = i;
                i += 1;
            }
            return j;
        })();
        """

        self.run(code, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

    def test_array_sum(self):
        code = """
        (function () {
            var i = 0;
            var j = [];
            while(i < 10) {
                j[i] = i;
                i += 1;
            }
            i = 0;
            var k = 0;
            while(i < j.length) {
                k += j[i];
                i += 1;
            }
            return k;
        })();
        """

        self.run(code, 45)

    def test_array_fill_2x_sum(self):
        code = """
        (function () {
            var i = 0;
            var j = [];
            while(i < 10) {
                j[i] = null;
                i += 1;
            }

            i = 0;
            while(i < 10) {
                j[i] = i;
                i += 1;
            }

            i = 0;
            var k = 0;
            while(i < j.length) {
                k += j[i];
                i += 1;
            }
            return k;
        })();
        """

        self.run(code, 45)
