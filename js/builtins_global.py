from pypy.rlib.rfloat import NAN, INFINITY, isnan, isinf
from js.jsobj import W_String
from js.execution import JsTypeError
from js.builtins import get_arg

def setup(global_object):
    from js.builtins import put_intimate_function, put_native_function, put_property
    from js.builtins_number import w_NAN
    from js.builtins_number import w_POSITIVE_INFINITY
    from js.jsobj import w_Undefined
    from pypy.rlib.objectmodel import we_are_translated

    # 15.1.1.1
    put_property(global_object, 'NaN', w_NAN, writable = False, enumerable = False, configurable = False)

    # 15.1.1.2
    put_property(global_object, 'Infinity', w_POSITIVE_INFINITY, writable = False, enumerable = False, configurable = False)

    # 15.1.1.3
    put_property(global_object, 'undefined', w_Undefined, writable = False, enumerable = False, configurable = False)

    # 15.1.2.1
    put_intimate_function(global_object, 'eval', js_eval, params = ['x'])

    # 15.1.2.2
    put_native_function(global_object, 'parseInt', parse_int, params = ['string', 'radix'])

    # 15.1.2.3
    put_native_function(global_object, 'parseFloat', parse_float, params = ['string'])

    # 15.1.2.4
    put_native_function(global_object, 'isNaN', is_nan, params = ['number'])

    # 15.1.2.5
    put_native_function(global_object, 'isFinite', is_finite, params = ['number'])

    put_native_function(global_object, 'alert', alert)

    put_native_function(global_object, 'print', printjs)

    put_native_function(global_object, 'escape', escape, params = ['string'])
    put_native_function(global_object, 'unescape', unescape, params = ['string'])

    put_native_function(global_object, 'version', version)

    ## debugging
    if not we_are_translated():
        put_native_function(global_object, 'pypy_repr', pypy_repr)
        put_native_function(global_object, 'inspect', inspect)

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
    NUMERALS = '0123456789abcdefghijklmnopqrstuvwxyz'
    string = get_arg(args, 0)
    radix = get_arg(args, 1)

    input_string = string.to_string()
    s = input_string.lstrip()
    sign = 1

    if s.startswith('-'):
        sign = -1
    if s.startswith('-') or s.startswith('+'):
        s = s[1:]

    r = radix.ToInt32()
    strip_prefix = True
    if r != 0:
        if r < 2 or r > 36:
            return NAN
        if r != 16:
            strip_prefix = False
    else:
        r = 10

    if strip_prefix:
        if len(s) >= 2 and (s.startswith('0x') or s.startswith('0X')):
            s = s[2:]
            r = 16
        # TODO this is not specified in ecma 5 but tests expect it and it's implemented in v8!
        elif len(s) > 1 and s.startswith('0'):
            r = 8

    numerals = NUMERALS[:r]
    exp = r'[%s]+' % (numerals)

    import re
    match_data = re.match(exp, s, re.I)
    if match_data:
        z = match_data.group()
    else:
        z = ''

    if z == '':
        return NAN

    try:
        try:
            number = int(float(int(z, r)))
            try:
                from pypy.rlib.rarithmetic import ovfcheck_float_to_int
                ovfcheck_float_to_int(number)
            except OverflowError:
                number = float(number)
        except OverflowError:
            number = INFINITY
        return sign * number
    except ValueError:
        pass

    return NAN

# 15.1.2.3
def parse_float(this, args):
    string = get_arg(args, 0)
    input_string = string.to_string()
    trimmed_string = input_string.lstrip()

    import re
    match_data = re.match(r'(?:[+-]?((?:(?:\d+)(?:\.\d*)?)|Infinity|(?:\.[0-9]+))(?:[eE][\+\-]?[0-9]*)?)', trimmed_string)
    if match_data is not None:
        try:
            number_string = match_data.group()
            number = float(number_string)
            return number
        except ValueError:
            pass

    return NAN

def alert(this, args):
    pass

def printjs(this, args):
    print ",".join([i.to_string() for i in args])

# B.2.1
def escape(this, args):
    CHARARCERS = u'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@*_+-./'
    string = get_arg(args, 0)
    r1 = string.to_string()
    r2 = len(r1)
    r = u''
    k = 0

    while k != r2:
        c = r1[k]
        r6 = ord(c)
        if c in CHARARCERS:
            # step 13
            s = c
        elif r6 < 256:
            # step 11
            s = '%%%02X' % (r6)
        else:
            s = '%%u%04X' % (r6)
        r += s
        k += 1

    return r


# B.2.2
def unescape(this, args):
    import re
    string = get_arg(args, 0)
    r1 = string.to_string()
    r2 = len(r1)

    r = u''
    k = 0

    while k != r2:
        c = r1[k]
        if c == '%':
            # 8. 9. 10.
            if (k > r2 - 6) or \
                (r1[k+1] != 'u') or \
                (not re.match(r'[0-9a-f]{4}', r1[k+2:k+6], re.I)):
                # got step 14
                if k > r2 - 3: # 14.
                    pass # goto step 18
                else:
                    if not re.match(r'[0-9a-f]{2}', r1[k+1:k+3], re.I): # 15.
                        pass # goto step 18
                    else:
                        # 16
                        hex_numeral = '00%s' % (r1[k+1:k+3])
                        number = int(hex_numeral, 16)
                        c = unichr(number)
                        #17
                        k += 2
            else:
                # 11.
                hex_numeral = r1[k+2:k+6]
                number = int(hex_numeral, 16)
                c = unichr(number)

                # 12.
                k += 5
        # step 18
        r += c
        k += 1

    return r


def pypy_repr(this, args):
    o = args[0]
    return repr(o)

def inspect(this, args):
    pass
    #import pdb; pdb.set_trace();

def version(this, args):
    return '1.0'

# 15.1.2.1
def js_eval(ctx):
    from js.astbuilder import parse_to_ast
    from js.jscode import ast_to_bytecode
    from js.jsobj import _w, W_String
    from js.functions import JsEvalCode
    from js.execution_context import EvalExecutionContext
    from pypy.rlib.parsing.parsing import ParseError
    from js.execution import JsSyntaxError

    args = ctx.argv()
    x = get_arg(args, 0)

    if not isinstance(x, W_String):
        return x

    src = x.to_string()
    try:
        ast = parse_to_ast(src)
    except ParseError, e:
        error = e.errorinformation.failure_reasons
        error_lineno = e.source_pos.lineno
        error_pos = e.source_pos.columnno
        error_src = src.encode('unicode_escape')
        error_msg = 'Syntax Error in: "%s":%d,%d' %(error_src, error_lineno, error_pos)
        raise JsSyntaxError(error_msg)

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
    f = get_arg(args, 0)
    filename = f.to_string()

    ast = load_file(filename)
    symbol_map = ast.symbol_map
    code = ast_to_bytecode(ast, symbol_map)

    f = JsEvalCode(code)
    calling_context = ctx._calling_context_
    ctx = EvalExecutionContext(f, calling_context = calling_context)
    f.run(ctx)
