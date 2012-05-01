import sys
from pypy import conftest
class o:
    view = False
    viewloops = True
conftest.option = o

from pypy.jit.metainterp.test.support import LLJitMixin

from js import interpreter
from js.jscode import JsCode, jitdriver

class TestLLtype(LLJitMixin):
    def test_append(self):
        code = """
          var x = {i:0};
          function f() {
            while(x.i < 100) {
              x = {i:x.i + 1};
            }
          }
          f();
        """
        jsint = interpreter.Interpreter()
        bytecode = JsCode()
        interpreter.load_source(code, '').emit(bytecode)
        func = bytecode.make_js_function()

        def interp_w(c):
            jitdriver.set_param("inlining", True)
            code_val = func.run(jsint.global_context)
        interp_w(1)
        self.meta_interp(interp_w, [6], listcomp=True, backendopt=True, listops=True)

