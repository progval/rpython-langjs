from js.astbuilder import make_ast_builder, make_eval_ast_builder
from js.jscode import JsCode

from pypy.rlib.objectmodel import we_are_translated

import js.builtins

TEST = False

def load_source(script_source, sourcename):
    return js.builtins.load_source(script_source, sourcename)

def load_file(filename):
    return js.builtins.load_file(filename)

class Interpreter(object):
    """Creates a js interpreter"""
    def __init__(self):
        self.global_context, self.w_Global, self.w_Object = js.builtins.setup_builtins(self)

    def run(self, script, interactive=False):
        """run the interpreter"""
        bytecode = JsCode()
        script.emit(bytecode)
        if not we_are_translated():
            # debugging
            self._code = bytecode
        func = bytecode.make_js_function()
        if interactive:
            return func._run_with_context(self.global_context)
        else:
            func._run_with_context(self.global_context)
