import sys
from pypy import conftest
class o:
    view = False
    viewloops = True
conftest.option = o

from pypy.jit.metainterp.test.support import LLJitMixin

from js import interpreter
from js.jscode import jitdriver

class TestLLtype(LLJitMixin):
    def test_append(self):
        #code = """
          #var x = {i:0};
          #function f() {
            #while(x.i < 100) {
              #x = {i:x.i + 1};
            #}
          #}
          #f();
        #"""
        code = """
            var i = 0;
            while(i < 100) {
                i += 1;
            }
            return i;
        """
        jsint = interpreter.Interpreter()

        def interp_w():
            #jitdriver.set_param("inlining", True)
            code_val = jsint.run_src(code)
            return code_val.ToNumber()
        #assert interp_w() == 100
        assert self.meta_interp(interp_w, [], listcomp=True, backendopt=True, listops=True) == 100

