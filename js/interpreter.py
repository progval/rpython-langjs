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
        from js.jsobj import W_BasicObject
        self.global_object = W_BasicObject()
        from js.builtins import setup_builtins
        setup_builtins(self.global_object)

    def run_ast(self, ast):
        symbol_map = ast.symbol_map

        from js.jscode import ast_to_bytecode
        code = ast_to_bytecode(ast, symbol_map)

        return self.run(code)

    def run_src(self, src):
        from js.astbuilder import parse_to_ast
        ast = parse_to_ast(src)
        return self.run_ast(ast)

    def run(self, code, interactive=False):
        from js.functions import JsGlobalCode
        c = JsGlobalCode(code)

        from js.execution_context import GlobalExecutionContext
        ctx = GlobalExecutionContext(c, self.global_object)

        return ctx.run()

        #"""run the interpreter"""
        #bytecode = JsCode()
        #script.emit(bytecode)
        #if not we_are_translated():
            ## debugging
            #self._code = bytecode
        #func = bytecode.make_js_function()
        #if interactive:
        #    return func._run_with_context(self.global_context)
        #else:
        #    func._run_with_context(self.global_context)
