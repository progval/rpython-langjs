import math
from js.jsobj import W_IntNumber

from pypy.rlib.rfloat import NAN, INFINITY, isnan, isinf

def floor(this, *args):
    if len(args) < 1:
        return NAN

    val = args[0].ToNumber()

    pos = math.floor(val)
    if isnan(val):
        pos = INFINITY

    return pos

def abs(this, *args):
    val = args[0]
    if isinstance(val, W_IntNumber):
        if val.ToInteger() > 0:
            return val # fast path
        return -val.ToInteger()
    return abs(args[0].ToNumber())

def rounds(args, this):
    return floorjs(args, this)

def pow(args, this):
    return math.pow(args[0].ToNumber(), args[1].ToNumber())

def sqrt(args, this):
    return math.sqrt(args[0].ToNumber())

def log(args, this):
    return math.log(args[0].ToNumber())

py_min = min
def min(this, *args):
    a = args[0].ToNumber()
    b = args[1].ToNumber()
    return py_min(a, b)

py_max = max
def max(this, *args):
    a = args[0].ToNumber()
    b = args[1].ToNumber()
    return py_max(a, b)

import time
from pypy.rlib import rrandom
_random = rrandom.Random(int(time.time()))

def random(this, *args):
    return _random.random()

