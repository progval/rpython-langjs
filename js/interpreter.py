from pypy.rlib.objectmodel import we_are_translated
from pypy.rlib.streamio import open_file_as_stream

import js.builtins

def load_file(filename):
    from js.astbuilder import parse_to_ast

    f = open_file_as_stream(str(filename))
    src = f.readall()
    usrc = unicode(src)
    ast = parse_to_ast(usrc)
    f.close()
    return ast

class Interpreter(object):
    """Creates a js interpreter"""
    def __init__(self):
        from js.jsobj import W_GlobalObject
        self.global_object = W_GlobalObject()
        from js.builtins import setup_builtins
        setup_builtins(self.global_object)
        self.setup_interpreter_builtins()
        from js.object_space import object_space
        object_space.global_object = self.global_object
        object_space.assign_proto(self.global_object)


    def setup_interpreter_builtins(self):
        global_object = self.global_object
        from js.builtins import put_native_function
        def js_trace(this, args):
            import pdb; pdb.set_trace()
        put_native_function(global_object, u'trace', js_trace)

        interp = self
        def js_load(this, args):
            filename = args[0].to_string()
            interp.js_load(str(filename))

        put_native_function(global_object, u'load', js_load)

        def js_debug(this, args):
            import js.globals
            js.globals.DEBUG = not js.globals.DEBUG
            return js.globals.DEBUG

        put_native_function(global_object, u'debug', js_debug)

    def js_load(self, filename):
        ast = load_file(filename)
        return self.run_ast(ast)

    def run_ast(self, ast):
        symbol_map = ast.symbol_map

        from js.jscode import ast_to_bytecode
        code = ast_to_bytecode(ast, symbol_map)

        return self.run(code)

    def run_src(self, src):
        from js.astbuilder import parse_to_ast
        ast = parse_to_ast(unicode(src))
        return self.run_ast(ast)

    def run(self, code, interactive=False):
        from js.functions import JsGlobalCode

        from js.jscode import JsCode
        assert isinstance(code, JsCode)
        c = JsGlobalCode(code)

        from js.object_space import object_space
        from js.execution_context import GlobalExecutionContext

        ctx = GlobalExecutionContext(c, self.global_object)
        object_space.global_context = ctx

        result = c.run(ctx)
        return result.value
