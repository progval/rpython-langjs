
""" Base operations implementations
"""

from js.jsobj import W_String, W_IntNumber, W_FloatNumber
from js.object_space import _w, isint, isstr, isfloat

from rpython.rlib.rarithmetic import ovfcheck
from rpython.rlib.rfloat import isnan, isinf
from rpython.rlib.objectmodel import specialize

from js.builtins.number import w_NAN, w_POSITIVE_INFINITY, w_NEGATIVE_INFINITY

import math


# 11.6.1, 11.6.3
def plus(lval, rval):
    lprim = lval.ToPrimitive()
    rprim = rval.ToPrimitive()

    if isinstance(lprim, W_String) or isinstance(rprim, W_String):
        sleft = lprim.to_string()
        sright = rprim.to_string()
        return W_String(sleft + sright)
    # hot path
    if isint(lprim) and isint(rprim):
        ileft = lprim.ToInteger()
        iright = rprim.ToInteger()
        try:
            return W_IntNumber(ovfcheck(ileft + iright))
        except OverflowError:
            return W_FloatNumber(float(ileft) + float(iright))
    else:
        fleft = lprim.ToNumber()
        fright = rprim.ToNumber()
        return W_FloatNumber(fleft + fright)


def increment(nleft, constval=1):
    if isint(nleft):
        return W_IntNumber(nleft.ToInteger() + constval)
    else:
        return plus(nleft, W_IntNumber(constval))


def decrement(ctx, nleft, constval=1):
    if isinstance(nleft, W_IntNumber):
        return W_IntNumber(nleft.ToInteger() - constval)
    else:
        return sub(ctx, nleft, W_IntNumber(constval))


def sub(ctx, nleft, nright):
    if isint(nleft) and isint(nright):
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
    if isint(nleft) and isint(nright):
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


def mod(ctx, w_left, w_right):
    left = w_left.ToNumber()
    right = w_right.ToNumber()

    if isnan(left) or isnan(right):
        return w_NAN

    if isinf(left) or right == 0:
        return w_NAN

    if isinf(right):
        return w_left

    if left == 0:
        return w_left

    return W_FloatNumber(math.fmod(left, right))


def sign(x):
    from math import copysign
    return copysign(1.0, x)


def sign_of(a, b):
    sign_a = sign(a)
    sign_b = sign(b)
    return sign_a * sign_b


def w_signed_inf(sign):
    if sign < 0.0:
        return w_NEGATIVE_INFINITY
    return w_POSITIVE_INFINITY


# 11.5.2
def division(ctx, nleft, nright):
    fleft = nleft.ToNumber()
    fright = nright.ToNumber()
    if isnan(fleft) or isnan(fright):
        return w_NAN

    if isinf(fleft) and isinf(fright):
        return w_NAN

    if isinf(fleft) and fright == 0:
        s = sign_of(fleft, fright)
        return w_signed_inf(s)

    if isinf(fright):
        return _w(0)

    if fleft == 0 and fright == 0:
        return w_NAN

    if fright == 0:
        s = sign_of(fleft, fright)
        return w_signed_inf(s)

    val = fleft / fright
    return W_FloatNumber(val)


@specialize.argtype(0, 1)
def _compare_gt(x, y):
    return x > y


@specialize.argtype(0, 1)
def _compare_ge(x, y):
    return x >= y


def _base_compare(x, y, _compare):
    if isint(x) and isint(y):
        return _compare(x.ToInteger(), y.ToInteger())

    if isfloat(x) and isfloat(y):
        n1 = x.ToNumber()
        n2 = x.ToNumber()
        return _compare(n1, n2)

    p1 = x.ToPrimitive('Number')
    p2 = y.ToPrimitive('Number')

    if not (isstr(p1) and isstr(p2)):
        n1 = p1.ToNumber()
        n2 = p2.ToNumber()
        return _compare(n1, n2)
    else:
        s1 = p1.to_string()
        s2 = p2.to_string()
        return _compare(s1, s2)


def compare_gt(x, y):
    return _base_compare(x, y, _compare_gt)


def compare_ge(x, y):
    return _base_compare(x, y, _compare_ge)


def compare_lt(x, y):
    return _base_compare(y, x, _compare_gt)


def compare_le(x, y):
    return _base_compare(y, x, _compare_ge)


# 11.9.3
def AbstractEC(x, y):
    """
    Implements the Abstract Equality Comparison x == y
    trying to be fully to the spec
    """
    if isint(x) and isint(y):
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
            return x.to_boolean() == x.to_boolean()
        # XXX rethink it here
        return x.to_string() == y.to_string()
    else:
        #step 14
        if (type1 == "undefined" and type2 == "null") or \
                (type1 == "null" and type2 == "undefined"):
            return True
        if type1 == "number" and type2 == "string":
            return AbstractEC(x, W_FloatNumber(y.ToNumber()))
        if type1 == "string" and type2 == "number":
            return AbstractEC(W_FloatNumber(x.ToNumber()), y)
        if type1 == "boolean":
            return AbstractEC(W_FloatNumber(x.ToNumber()), y)
        if type2 == "boolean":
            return AbstractEC(x, W_FloatNumber(y.ToNumber()))
        if (type1 == "string" or type1 == "number") and \
                type2 == "object":
            return AbstractEC(x, y.ToPrimitive())
        if (type2 == "string" or type2 == "number") and \
                type1 == "object":
            return AbstractEC(x.ToPrimitive(), y)
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


def StrictEC(x, y):
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
        return x.to_boolean() == x.to_boolean()
    return x == y


def uminus(obj, ctx):
    if isint(obj):
        intval = obj.ToInteger()
        if intval == 0:
            return W_FloatNumber(-float(intval))
        return W_IntNumber(-intval)
    return W_FloatNumber(-obj.ToNumber())
