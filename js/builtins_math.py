import math
from js.jsobj import W_IntNumber

from pypy.rlib.rfloat import NAN, INFINITY, isnan, isinf

# 15.8.2.9
def floor(this, *args):
    if len(args) < 1:
        return NAN

    val = args[0].ToNumber()

    pos = math.floor(val)
    if isnan(val):
        pos = INFINITY

    return pos

# 15.8.2.1
def abs(this, *args):
    val = args[0]
    if isinstance(val, W_IntNumber):
        if val.ToInteger() > 0:
            return val # fast path
        return -val.ToInteger()
    return abs(args[0].ToNumber())

# 15.8.2.15
def round(this, *args):
    return floor(this, args)

# 15.8.2.13
def pow(this, *args):
    return math.pow(args[0].ToNumber(), args[1].ToNumber())

# 15.8.2.17
def sqrt(this, *args):
    return math.sqrt(args[0].ToNumber())

# 15.8.2.10
def log(this, *args):
    return math.log(args[0].ToNumber())

# 15.8.2.11
py_min = min
def min(this, *args):
    a = args[0].ToNumber()
    b = args[1].ToNumber()
    return py_min(a, b)

# 15.8.2.12
py_max = max
def max(this, *args):
    a = args[0].ToNumber()
    b = args[1].ToNumber()
    return py_max(a, b)

import time
from pypy.rlib import rrandom
_random = rrandom.Random(int(time.time()))

# 15.8.2.14
# 15.8.1.1
E = math.e

# 15.8.1.2
LN10 = math.log(10)

# 15.8.1.3
LN2 = math.log(2)

# 15.8.1.4
LOG2E = math.log(math.e) / math.log(2)

# 15.8.1.5
LOG10E = math.log10(math.e)

# 15.8.1.6
PI = math.pi

# 15.8.1.7
SQRT1_2 = math.sqrt(0.5)

# 15.8.1.8
SQRT2 = math.sqrt(2)
def random(this, *args):
    return _random.random()

