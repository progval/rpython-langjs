from rpython.rlib.streamio import open_file_as_stream


def load_file(filename):
    f = open_file_as_stream(str(filename))
    src = f.readall()
    return src


class InterpreterConfig(object):
    def __init__(self, config={}):
        self.debug = config.get('debug', False)


class Interpreter(object):
    """Creates a js interpreter"""
    def __init__(self, config={}):
        from js.jsobj import W_GlobalObject
        from js.object_space import object_space
        import js.builtins.interpreter

        self.config = InterpreterConfig(config)
        self.global_object = W_GlobalObject()
        object_space.global_object = self.global_object
        object_space.interpreter = self

        js.builtins.setup_builtins(self.global_object)
        js.builtins.interpreter.setup_builtins(self.global_object)

        object_space.assign_proto(self.global_object)

    def run_ast(self, ast):
        symbol_map = ast.symbol_map

        from js.jscode import ast_to_bytecode
        code = ast_to_bytecode(ast, symbol_map)

        return self.run(code)

    def run_src(self, src):
        from js.astbuilder import parse_to_ast
        from js.runistr import decode_str_utf8
        ast = parse_to_ast(decode_str_utf8(src))
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
