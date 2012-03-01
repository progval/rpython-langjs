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
    s = args[0].ToString().strip(" ")
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
    s = args[0].ToString().strip(" ")
    try:
        n = float(s)
    except ValueError:
        n = NAN
    return n

def alert(this, args):
    pass

def writer(x):
    print x

def printjs(this, args):
    writer(",".join([i.ToString() for i in args]))

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
    strval = w_string.ToString()
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

