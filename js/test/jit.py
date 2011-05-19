import sys
from pypy import conftest
class o:
    view = False
    viewloops = True
conftest.option = o

from pypy.jit.metainterp.test.test_basic import LLJitMixin

from js import interpreter
from js.jscode import JsCode, jitdriver
from js.jsobj import ExecutionContext

class TestLLtype(LLJitMixin):
    def test_append(self):
        code = """
        function f() {
            for(i = 0; i < 100; i++){
            }
        }
        f();
        """
        jsint = interpreter.Interpreter()
        ctx = jsint.w_Global
        bytecode = JsCode()
        interpreter.load_source(code, '').emit(bytecode)
        func = bytecode.make_js_function()

        def interp_w(c):
            jitdriver.set_param("inlining", True)
            code_val = func.run(ExecutionContext([ctx]))
        interp_w(1)
        self.meta_interp(interp_w, [6], listcomp=True, backendopt=True, listops=True)

