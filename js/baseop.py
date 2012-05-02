
""" Base operations implementations
"""

from js.jsobj import W_String, W_IntNumber, W_FloatNumber
from js.execution import ThrowException, JsTypeError

from pypy.rlib.rarithmetic import r_uint, intmask, ovfcheck
from pypy.rlib.rfloat import  INFINITY, NAN, isnan, isinf

import math

def plus(ctx, nleft, nright):
    if isinstance(nleft, W_String) or isinstance(nright, W_String):
        sleft = nleft.to_string()
        sright = nright.to_string()
        return W_String(sleft + sright)
    # hot path
    if isinstance(nleft, W_IntNumber) and isinstance(nright, W_IntNumber):
        ileft = nleft.ToInteger()
        iright = nright.ToInteger()
        try:
            return W_IntNumber(ovfcheck(ileft + iright))
        except OverflowError:
            return W_FloatNumber(float(ileft) + float(iright))
    else:
        fleft = nleft.ToNumber()
        fright = nright.ToNumber()
        return W_FloatNumber(fleft + fright)

def increment(ctx, nleft, constval=1):
    if isinstance(nleft, W_IntNumber):
        return W_IntNumber(nleft.ToInteger() + constval)
    else:
        return plus(ctx, nleft, W_IntNumber(constval))

def decrement(ctx, nleft, constval=1):
    if isinstance(nleft, W_IntNumber):
        return W_IntNumber(nleft.ToInteger() - constval)
    else:
        return sub(ctx, nleft, W_IntNumber(constval))

def sub(ctx, nleft, nright):
    if isinstance(nleft, W_IntNumber) and isinstance(nright, W_IntNumber):
        # XXX fff
        ileft = nleft.ToInt32()
        iright = nright.ToInt32()
        try:
            return W_IntNumber(ovfcheck(ileft - iright))
        except OverflowError:
            return W_FloatNumber(float(ileft) - float(iright))
    fleft = nleft.ToNumber()
    fright = nright.ToNumber()
    return W_FloatNumber(fleft - fright)

def mult(ctx, nleft, nright):
    if isinstance(nleft, W_IntNumber) and isinstance(nright, W_IntNumber):
        # XXXX test & stuff
        ileft = nleft.ToInteger()
        iright = nright.ToInteger()
        try:
            return W_IntNumber(ovfcheck(ileft * iright))
        except OverflowError:
            return W_FloatNumber(float(ileft) * float(iright))
    fleft = nleft.ToNumber()
    fright = nright.ToNumber()
    return W_FloatNumber(fleft * fright)

def mod(ctx, nleft, nright): # XXX this one is really not following spec
    fleft = nleft.ToNumber()
    fright = nright.ToNumber()
    return W_FloatNumber(math.fmod(fleft, fright))

def division(ctx, nleft, nright):
    # XXX optimise for ints and floats
    fleft = nleft.ToNumber()
    fright = nright.ToNumber()
    if fright == 0:
        if fleft < 0:
            val = -INFINITY
        elif fleft == 0:
            val = NAN
        else:
            val = INFINITY
    else:
        val = fleft / fright
    return W_FloatNumber(val)

def compare(ctx, x, y):
    if isinstance(x, W_IntNumber) and isinstance(y, W_IntNumber):
        return x.ToInteger() > y.ToInteger()
    if isinstance(x, W_FloatNumber) and isinstance(y, W_FloatNumber):
        if isnan(x.ToNumber()) or isnan(y.ToNumber()):
            return -1
        return x.ToNumber() > y.ToNumber()
    s1 = x.ToPrimitive('Number')
    s2 = y.ToPrimitive('Number')
    if not (isinstance(s1, W_String) and isinstance(s2, W_String)):
        s4 = s1.ToNumber()
        s5 = s2.ToNumber()
        if isnan(s4) or isnan(s5):
            return False
        return s4 > s5
    else:
        s4 = s1.to_string()
        s5 = s2.to_string()
        return s4 > s5

def compare_e(ctx, x, y):
    if isinstance(x, W_IntNumber) and isinstance(y, W_IntNumber):
        return x.ToInteger() >= y.ToInteger()
    if isinstance(x, W_FloatNumber) and isinstance(y, W_FloatNumber):
        if isnan(x.ToNumber()) or isnan(y.ToNumber()):
            return -1
        return x.ToNumber() >= y.ToNumber()
    s1 = x.ToPrimitive('Number')
    s2 = y.ToPrimitive('Number')
    if not (isinstance(s1, W_String) and isinstance(s2, W_String)):
        s4 = s1.ToNumber()
        s5 = s2.ToNumber()
        if isnan(s4) or isnan(s5):
            return False
        return s4 >= s5
    else:
        s4 = s1.to_string()
        s5 = s2.to_string()
        return s4 >= s5

def AbstractEC(ctx, x, y):
    """
    Implements the Abstract Equality Comparison x == y
    trying to be fully to the spec
    """
    if isinstance(x, W_IntNumber) and isinstance(y, W_IntNumber):
        return x.ToInteger() == y.ToInteger()
    if isinstance(x, W_FloatNumber) and isinstance(y, W_FloatNumber):
        if isnan(x.ToNumber()) or isnan(y.ToNumber()):
            return False
        return x.ToNumber() == y.ToNumber()
    type1 = x.type()
    type2 = y.type()
    if type1 == type2:
        if type1 == "undefined" or type1 == "null":
            return True
        if type1 == "number":
            n1 = x.ToNumber()
            n2 = y.ToNumber()
            if isnan(n1) or isnan(n2):
                return False
            if n1 == n2:
                return True
            return False
        elif type1 == "string":
            return x.to_string() == y.to_string()
        elif type1 == "boolean":
            return x.ToBoolean() == x.ToBoolean()
        # XXX rethink it here
        return x.to_string() == y.to_string()
    else:
        #step 14
        if (type1 == "undefined" and type2 == "null") or \
           (type1 == "null" and type2 == "undefined"):
            return True
        if type1 == "number" and type2 == "string":
            return AbstractEC(ctx, x, W_FloatNumber(y.ToNumber()))
        if type1 == "string" and type2 == "number":
            return AbstractEC(ctx, W_FloatNumber(x.ToNumber()), y)
        if type1 == "boolean":
            return AbstractEC(ctx, W_FloatNumber(x.ToNumber()), y)
        if type2 == "boolean":
            return AbstractEC(ctx, x, W_FloatNumber(y.ToNumber()))
        if (type1 == "string" or type1 == "number") and \
            type2 == "object":
            return AbstractEC(ctx, x, y.ToPrimitive())
        if (type2 == "string" or type2 == "number") and \
            type1 == "object":
            return AbstractEC(ctx, x.ToPrimitive(), y)
        return False


    objtype = x.GetValue().type()
    if objtype == y.GetValue().type():
        if objtype == "undefined" or objtype == "null":
            return True

    if isinstance(x, W_String) and isinstance(y, W_String):
        r = x.to_string() == y.to_string()
    else:
        r = x.ToNumber() == y.ToNumber()
    return r

def StrictEC(ctx, x, y):
    """
    Implements the Strict Equality Comparison x === y
    trying to be fully to the spec
    """
    type1 = x.type()
    type2 = y.type()
    if type1 != type2:
        return False
    if type1 == "undefined" or type1 == "null":
        return True
    if type1 == "number":
        n1 = x.ToNumber()
        n2 = y.ToNumber()
        if isnan(n1) or isnan(n2):
            return False
        if n1 == n2:
            return True
        return False
    if type1 == "string":
        return x.to_string() == y.to_string()
    if type1 == "boolean":
        return x.ToBoolean() == x.ToBoolean()
    return x == y


def commonnew(ctx, obj, args):
    from js.jsobj import W_BasicObject
    if not isinstance(obj, W_BasicObject):
        raise ThrowException(W_String('it is not a constructor'))
    try:
        res = obj.Construct(args=args)
        return res
    except JsTypeError:
        raise ThrowException(W_String('it is not a constructor'))
    return res

def uminus(obj, ctx):
    if isinstance(obj, W_IntNumber):
        return W_IntNumber(-obj.ToInteger())
    return W_FloatNumber(-obj.ToNumber())
