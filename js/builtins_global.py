from pypy.rlib.rfloat import NAN, INFINITY, isnan, isinf
from js.jsobj import W_String
from js.execution import JsTypeError

# 15.1.2.4
def is_nan(this, args):
    if len(args) < 1:
        return True
    return isnan(args[0].ToNumber())

# 15.1.2.5
def is_finite(this, args):
    if len(args) < 1:
        return True
    n = args[0].ToNumber()
    if  isinf(n) or isnan(n):
        return False
    else:
        return True

# 15.1.2.2
def parse_int(this, args):
    if len(args) < 1:
        return NAN
    s = args[0].to_string().strip(" ")
    if len(args) > 1:
        radix = args[1].ToInt32()
    else:
        radix = 10
    if len(s) >= 2 and (s.startswith('0x') or s.startswith('0X')) :
        radix = 16
        s = s[2:]
    if s == '' or radix < 2 or radix > 36:
        return NAN
    try:
        n = int(s, radix)
    except ValueError:
        return NAN
    return n

# 15.1.2.3
def parse_float(this, args):
    if len(args) < 1:
        return NAN
    s = args[0].to_string().strip(" ")
    try:
        n = float(s)
    except ValueError:
        n = NAN
    return n

def alert(this, args):
    pass

def printjs(this, args):
    print ",".join([i.to_string() for i in args])

def _ishex(ch):
    return ((ch >= 'a' and ch <= 'f') or (ch >= '0' and ch <= '9') or
            (ch >= 'A' and ch <= 'F'))

def unescape(this, args):
    # XXX consider using StringBuilder here
    res = []
    w_string = args[0]
    if not isinstance(w_string, W_String):
        raise JsTypeError(W_String("Expected string"))
    assert isinstance(w_string, W_String)
    strval = w_string.to_string()
    lgt = len(strval)
    i = 0
    while i < lgt:
        ch = strval[i]
        if ch == '%':
            if (i + 2 < lgt and _ishex(strval[i+1]) and _ishex(strval[i+2])):
                ch = chr(int(strval[i + 1] + strval[i + 2], 16))
                i += 2
            elif (i + 5 < lgt and strval[i + 1] == 'u' and
                  _ishex(strval[i + 2]) and _ishex(strval[i + 3]) and
                  _ishex(strval[i + 4]) and _ishex(strval[i + 5])):
                ch = chr(int(strval[i+2:i+6], 16))
                i += 5
        i += 1
        res.append(ch)
    return ''.join(res)

def pypy_repr(this, args):
    o = args[0]
    return repr(o)

def inspect(this, args):
    pass
    #import pdb; pdb.set_trace();

def version(this, args):
    return '1.0'

def js_eval(ctx):
    from js.astbuilder import parse_to_ast
    from js.jscode import ast_to_bytecode
    from js.jsobj import _w
    from js.functions import JsEvalCode
    from js.execution_context import EvalExecutionContext

    args = ctx.argv()
    src = args[0].to_string()

    from pypy.rlib.parsing.parsing import ParseError
    try:
        ast = parse_to_ast(src)
    except ParseError, e:
        from js.execution import JsSyntaxError
        raise JsSyntaxError()

    symbol_map = ast.symbol_map
    code = ast_to_bytecode(ast, symbol_map)

    f = JsEvalCode(code)
    calling_context = ctx._calling_context_
    ctx = EvalExecutionContext(f, calling_context = calling_context)
    res = f.run(ctx)
    return _w(res)

def js_load(ctx):
    from js.interpreter import load_file
    from js.jscode import ast_to_bytecode
    from js.functions import JsEvalCode
    from js.execution_context import EvalExecutionContext

    args = ctx.argv()
    filename = args[0].to_string()

    ast = load_file(filename)
    symbol_map = ast.symbol_map
    code = ast_to_bytecode(ast, symbol_map)

    f = JsEvalCode(code)
    calling_context = ctx._calling_context_
    ctx = EvalExecutionContext(f, calling_context = calling_context)
    f.run(ctx)
