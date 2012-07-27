from pypy.rlib.objectmodel import we_are_translated
from pypy.rlib.streamio import open_file_as_stream

def load_file(filename):
    from js.astbuilder import parse_to_ast
    from runistr import decode_str_utf8

    f = open_file_as_stream(str(filename))
    src = f.readall()
    usrc = decode_str_utf8(src)
    assert usrc is not None
    ast = parse_to_ast(usrc)
    f.close()
    return ast

class Interpreter(object):
    """Creates a js interpreter"""
    def __init__(self):
        from js.jsobj import W_GlobalObject
        from js.object_space import object_space
        import js.builtins
        import js.builtins_interpreter

        self.global_object = W_GlobalObject()
        object_space.global_object = self.global_object
        object_space.interpreter = self

        js.builtins.setup_builtins(self.global_object)
        js.builtins_interpreter.setup_builtins(self.global_object, overwrite_eval = True)

        object_space.assign_proto(self.global_object)

    def run_file(self, filename):
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
