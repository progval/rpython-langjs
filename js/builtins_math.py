import math
from js.jsobj import _w

from pypy.rlib.rfloat import NAN, INFINITY, isnan, isinf
from js.builtins import get_arg

def setup(global_object):
    from js.builtins import put_native_function, put_property
    from js.jsobj import W_Math
    # 15.8
    w_Math = W_Math()
    put_property(global_object, 'Math', w_Math)

    put_native_function(w_Math, 'abs', js_abs)
    put_native_function(w_Math, 'floor', floor)
    put_native_function(w_Math, 'round', js_round)
    put_native_function(w_Math, 'random', random)
    put_native_function(w_Math, 'min', js_min)
    put_native_function(w_Math, 'max', js_max)
    put_native_function(w_Math, 'pow', pow)
    put_native_function(w_Math, 'sqrt', sqrt)
    put_native_function(w_Math, 'log', log)

    # 15.8.1

    # 15.8.1.1
    put_property(w_Math, 'E', _w(E), writable = False, enumerable = False, configurable = False)

    # 15.8.1.2
    put_property(w_Math, 'LN10', _w(LN10), writable = False, enumerable = False, configurable = False)

    # 15.8.1.3
    put_property(w_Math, 'LN2', _w(LN2), writable = False, enumerable = False, configurable = False)

    # 15.8.1.4
    put_property(w_Math, 'LOG2E', _w(LOG2E), writable = False, enumerable = False, configurable = False)

    # 15.8.1.5
    put_property(w_Math, 'LOG10E', _w(LOG10E), writable = False, enumerable = False, configurable = False)

    # 15.8.1.6
    put_property(w_Math, 'PI', _w(PI), writable = False, enumerable = False, configurable = False)

    # 15.8.1.7
    put_property(w_Math, 'SQRT1_2', _w(SQRT1_2), writable = False, enumerable = False, configurable = False)

    # 15.8.1.8
    put_property(w_Math, 'SQRT2', _w(SQRT2), writable = False, enumerable = False, configurable = False)

# 15.8.2.9
def floor(this, args):
    if len(args) < 1:
        return NAN

    val = args[0].ToNumber()

    pos = math.floor(val)
    if isnan(val):
        pos = INFINITY

    return pos

# 15.8.2.1
def js_abs(this, args):
    val = args[0]
    return abs(val.ToNumber())

# 15.8.2.15
def js_round(this, args):
    return floor(this, args)

def isodd(i):
    isinstance(i, int) and i % 2 == 1

# 15.8.2.13
def pow(this, args):
    w_x = get_arg(args, 0)
    w_y = get_arg(args, 1)
    x = w_x.ToNumber()
    y = w_y.ToNumber()

    if isnan(y):
        return NAN
    if y == 0:
        return 1
    if isnan(x):
        return NAN
    if abs(x) > 1 and y == INFINITY:
        return INFINITY
    if abs(x) > 1 and y == -INFINITY:
        return 0
    if abs(x) == 1 and isinf(y):
        return NAN
    if abs(x) < 1 and y == INFINITY:
        return 0
    if abs(x) < 1 and y == -INFINITY:
        return INFINITY
    if x == INFINITY and y > 0:
        return INFINITY
    if x == INFINITY and y < 0:
        return 0
    if x == -INFINITY and y > 0 and isodd(y):
        return -INFINITY
    if x == -INFINITY and y > 0 and not isodd(y):
        return INFINITY
    if x == -INFINITY and y < 0 and isodd(y):
        return -0
    if x == -INFINITY and y < 0 and not isodd(y):
        return 0
    if x == 0 and y > 0:
        return 0
    if x == 0 and y < 0:
        return INFINITY
    if x == -0 and y > 0 and isodd(y):
        return -0
    if x == -0 and y > 0 and not isodd(y):
        return +0
    if x == -0 and y < 0 and isodd(y):
        return -INFINITY
    if x == -0 and y < 0 and not isodd(y):
        return INFINITY
    if x < 0 and not isinstance(y, int):
        return NAN

    try:
        return math.pow(x, y)
    except OverflowError:
        return INFINITY

# 15.8.2.17
def sqrt(this, args):
    return math.sqrt(args[0].ToNumber())

# 15.8.2.10
def log(this, args):
    return math.log(args[0].ToNumber())

# 15.8.2.11
def js_min(this, args):
    a = args[0].ToNumber()
    b = args[1].ToNumber()
    return min(a, b)

# 15.8.2.12
def js_max(this, args):
    a = args[0].ToNumber()
    b = args[1].ToNumber()
    return max(a, b)

import time
from pypy.rlib import rrandom
_random = rrandom.Random(int(time.time()))

# 15.8.2.14
def random(this, args):
    return _random.random()

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
