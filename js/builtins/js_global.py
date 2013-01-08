# -*- coding: utf-8 -*-

from pypy.rlib.rfloat import NAN, INFINITY, isnan, isinf
from js.builtins import get_arg
from js.object_space import w_return
from pypy.module.unicodedata import unicodedb


def setup(global_object):
    from js.builtins import put_intimate_function, put_native_function, put_property
    from js.builtins.number import w_NAN
    from js.builtins.number import w_POSITIVE_INFINITY
    from pypy.rlib.objectmodel import we_are_translated
    from js.object_space import newundefined

    # 15.1.1.1
    put_property(global_object, u'NaN', w_NAN, writable=False, enumerable=False, configurable=False)

    # 15.1.1.2
    put_property(global_object, u'Infinity', w_POSITIVE_INFINITY, writable=False, enumerable=False, configurable=False)

    # 15.1.1.3
    put_property(global_object, u'undefined', newundefined(), writable=False, enumerable=False, configurable=False)

    # 15.1.2.1
    put_intimate_function(global_object, u'eval', js_eval, params=[u'x'])

    # 15.1.2.2
    put_native_function(global_object, u'parseInt', parse_int, params=[u'string', u'radix'])

    # 15.1.2.3
    # TODO
    put_native_function(global_object, u'parseFloat', parse_float, params=[u'string'])

    # 15.1.2.4
    put_native_function(global_object, u'isNaN', is_nan, params=[u'number'])

    # 15.1.2.5
    put_native_function(global_object, u'isFinite', is_finite, params=[u'number'])

    put_native_function(global_object, u'alert', alert)

    put_native_function(global_object, u'print', printjs)

    put_native_function(global_object, u'escape', escape, params=[u'string'])

    put_native_function(global_object, u'unescape', unescape, params=[u'string'])

    put_native_function(global_object, u'version', version)

    ## debugging
    if not we_are_translated():
        put_native_function(global_object, u'pypy_repr', pypy_repr)
        put_native_function(global_object, u'inspect', inspect)


# 15.1.2.4
@w_return
def is_nan(this, args):
    if len(args) < 1:
        return True
    return isnan(args[0].ToNumber())


# 15.1.2.5
@w_return
def is_finite(this, args):
    if len(args) < 1:
        return True
    n = args[0].ToNumber()
    if isinf(n) or isnan(n):
        return False
    else:
        return True


def _isspace(uchar):
    return unicodedb.isspace(ord(uchar))


def _strip(unistr, left=True, right=True):
    lpos = 0
    rpos = len(unistr)

    if left:
        while lpos < rpos and _isspace(unistr[lpos]):
            lpos += 1

    if right:
        while rpos > lpos and _isspace(unistr[rpos - 1]):
            rpos -= 1

    assert rpos >= 0
    result = unistr[lpos:rpos]
    return result


def _lstrip(unistr):
    return _strip(unistr, right=False)


def _string_match_chars(string, chars):
    for char in string:
        c = unichr(unicodedb.tolower(ord(char)))
        if c not in chars:
            return False
    return True


# 15.1.2.2
@w_return
def parse_int(this, args):
    string = get_arg(args, 0)
    radix = get_arg(args, 1)

    return _parse_int(string.to_string(), radix.ToInt32())


def _parse_int(string, radix):
    assert isinstance(string, unicode)
    NUMERALS = u'0123456789abcdefghijklmnopqrstuvwxyz'
    input_string = string
    s = _strip(input_string)
    sign = 1

    if s.startswith(u'-'):
        sign = -1
    if s.startswith(u'-') or s.startswith(u'+'):
        s = s[1:]

    r = radix
    strip_prefix = True

    if r != 0:
        if r < 2 or r > 36:
            return NAN
        if r != 16:
            strip_prefix = False
    else:
        r = 10

    if strip_prefix:
        if len(s) >= 2 and (s.startswith(u'0x') or s.startswith(u'0X')):
            s = s[2:]
            r = 16
        # TODO this is not specified in ecma 5 but tests expect it and it's implemented in v8!
        elif len(s) > 1 and s.startswith(u'0'):
            r = 8

    numerals = NUMERALS[:r]

    z = []
    for char in s:
        uni_ord = unicodedb.tolower(ord(char))
        if uni_ord > 128:
            break
        c = chr(uni_ord)
        if c not in numerals:
            break
        z.append(c)

    if not z:
        return NAN

    num_str = ''.join(z)

    try:
        number = int(num_str, r)
        try:
            from pypy.rlib.rarithmetic import ovfcheck_float_to_int
            ovfcheck_float_to_int(number)
        except OverflowError:
            number = float(number)
        return sign * number
    except OverflowError:
        return INFINITY
    except ValueError:
        pass

    return NAN


# 15.1.2.3
@w_return
def parse_float(this, args):
    from js.runistr import encode_unicode_utf8
    from js.constants import num_lit_rexp

    string = get_arg(args, 0)
    input_string = string.to_string()
    trimmed_string = _strip(input_string)
    str_trimmed_string = encode_unicode_utf8(trimmed_string)

    match_data = num_lit_rexp.match(str_trimmed_string)
    if match_data is not None:
        number_string = match_data.group()
    else:
        number_string = ''

    if number_string == 'Infinity' or number_string == '+Infinity':
        return INFINITY
    elif number_string == '-Infinity':
        return -INFINITY

    try:
        number = float(number_string)
        return number
    except ValueError:
        pass

    return NAN


@w_return
def alert(this, args):
    printjs(this, args)


@w_return
def printjs(this, args):
    if len(args) == 0:
        return

    from pypy.rlib.rstring import UnicodeBuilder
    from js.runistr import encode_unicode_utf8

    builder = UnicodeBuilder()
    for arg in args[:-1]:
        builder.append(arg.to_string())
        builder.append(u',')

    builder.append(args[-1].to_string())

    u_print_str = builder.build()
    print_str = encode_unicode_utf8(u_print_str)
    print(print_str)


def hexing(i, length):
    h = unicode(hex(i).upper())
    assert h.startswith('0X')
    h = h[2:]

    while(len(h) < length):
        h = u'0' + h

    return h


# B.2.1
@w_return
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
            s = u'%' + hexing(r6, 2)
        else:
            s = u'%u' + hexing(r6, 4)
        r += s
        k += 1

    return r


# B.2.2
@w_return
def unescape(this, args):
    string = get_arg(args, 0)
    r1 = string.to_string()
    r2 = len(r1)

    r = u''
    k = 0
    hexchars = u'0123456789abcdef'

    while k != r2:
        c = r1[k]
        if c == u'%':
            # 8. 9. 10.
            if (k > r2 - 6) or (r1[k + 1] != u'u') or (not len(r1) == 6 and _string_match_chars(r1[k + 2:k + 6], hexchars)):
                # got step 14
                if k > r2 - 3:  # 14.
                    pass  # goto step 18
                else:
                    if not _string_match_chars(r1[k + 1:k + 3], hexchars):  # 15.
                        pass  # goto step 18
                    else:
                        # 16
                        hex_numeral = u'00' + r1[k + 1:k + 3]
                        number = int(str(hex_numeral), 16)
                        c = unichr(number)
                        #17
                        k += 2
            else:
                # 11.
                hex_numeral = r1[k + 2:k + 6]
                number = int(str(hex_numeral), 16)
                c = unichr(number)

                # 12.
                k += 5
        # step 18
        r += c
        k += 1

    return r


@w_return
def pypy_repr(this, args):
    o = args[0]
    return str(o)


@w_return
def inspect(this, args):
    pass


@w_return
def version(this, args):
    return '1.0'


# 15.1.2.1
def js_eval(ctx):
    from js.astbuilder import parse_to_ast
    from js.jscode import ast_to_bytecode
    from js.jsobj import W_String
    from js.functions import JsEvalCode
    from js.execution_context import EvalExecutionContext
    from pypy.rlib.parsing.parsing import ParseError
    from pypy.rlib.parsing.deterministic import LexerError
    from js.astbuilder import FakeParseError
    from js.execution import JsSyntaxError

    args = ctx.argv()
    x = get_arg(args, 0)

    if not isinstance(x, W_String):
        from js.completion import NormalCompletion
        return NormalCompletion(value=x)

    src = x.to_string()

    try:
        ast = parse_to_ast(src)
    except ParseError, e:
        #error = e.errorinformation.failure_reasons
        #error_lineno = e.source_pos.lineno
        #error_pos = e.source_pos.columnno
        #raise JsSyntaxError(msg = unicode(error), src = unicode(src), line = error_lineno, column = error_pos)
        raise JsSyntaxError()
    except FakeParseError, e:
        #raise JsSyntaxError(msg = unicode(e.msg), src = unicode(src))
        raise JsSyntaxError()
    except LexerError, e:
        #error_lineno = e.source_pos.lineno
        #error_pos = e.source_pos.columnno
        error_msg = u'LexerError'
        #raise JsSyntaxError(msg = error_msg, src = unicode(src), line = error_lineno, column = error_pos)
        raise JsSyntaxError(msg=error_msg)

    symbol_map = ast.symbol_map
    code = ast_to_bytecode(ast, symbol_map)

    f = JsEvalCode(code)
    calling_context = ctx._calling_context_

    ctx = EvalExecutionContext(f, calling_context=calling_context)
    res = f.run(ctx)
    return res


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
    ctx = EvalExecutionContext(f, calling_context=calling_context)
    f.run(ctx)
