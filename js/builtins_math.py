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

    put_native_function(w_Math, 'abs', js_abs, params = ['x'])
    put_native_function(w_Math, 'floor', floor)
    put_native_function(w_Math, 'round', js_round)
    put_native_function(w_Math, 'random', random)
    put_native_function(w_Math, 'min', js_min, params = ['value1', 'value2'])
    put_native_function(w_Math, 'max', js_max, params = ['value1', 'value2'])
    put_native_function(w_Math, 'pow', js_pow, params = ['x', 'y'])
    put_native_function(w_Math, 'sqrt', js_sqrt, params = ['x'])
    put_native_function(w_Math, 'log', js_log, params = ['x'])
    put_native_function(w_Math, 'sin', js_sin, params = ['x'])
    put_native_function(w_Math, 'tan', js_tan, params = ['x'])
    put_native_function(w_Math, 'acos', js_acos, params = ['x'])
    put_native_function(w_Math, 'asin', js_asin, params = ['x'])
    put_native_function(w_Math, 'atan', js_atan, params = ['x'])
    put_native_function(w_Math, 'atan2', js_atan2, params = ['y', 'x'])
    put_native_function(w_Math, 'ceil', js_ceil, params = ['x'])
    put_native_function(w_Math, 'cos', js_cos, params = ['x'])


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
    arg0 = get_arg(args, 0)
    x = arg0.ToNumber()

    if isnan(x):
        return NAN

    return abs(x)

# 15.8.2.15
def js_round(this, args):
    return floor(this, args)

def isodd(i):
    isinstance(i, int) and i % 2 == 1

# 15.8.2.13
def js_pow(this, args):
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
def js_sqrt(this, args):
    arg0 = get_arg(args, 0)
    x = arg0.ToNumber()

    if isnan(x):
        return NAN

    if x < 0:
        return NAN

    if isinf(x):
        return INFINITY

    return math.sqrt(x)

# 15.8.2.10
def js_log(this, args):
    arg0 = get_arg(args, 0)
    x = arg0.ToNumber()

    if isnan(x):
        return NAN

    if x < 0:
        return NAN

    if x == 0:
        return -INFINITY

    if x == INFINITY:
        return INFINITY

    return math.log(x)

# 15.8.2.11
def js_min(this, args):
    values = []
    for arg in args:
        value = arg.ToNumber()
        if isnan(value):
            return NAN
        values.append(value)

    if not values:
        return INFINITY

    return min(values)

# 15.8.2.12
def js_max(this, args):
    values = []
    for arg in args:
        value = arg.ToNumber()
        if isnan(value):
            return NAN
        values.append(value)

    if not values:
        return -INFINITY

    return max(values)

# 15.8.2.17
def js_sin(this, args):
    arg0 = get_arg(args, 0)
    x = arg0.ToNumber()

    if isnan(x) or isinf(x):
        return NAN

    if x < 0:
        return NAN

    return math.sin(x)

# 15.8.2.18
def js_tan(this, args):
    arg0 = get_arg(args, 0)
    x = arg0.ToNumber()

    if isnan(x) or isinf(x):
        return NAN

    if x < 0:
        return NAN

    return math.tan(x)

# 15.8.2.2
def js_acos(this, args):
    arg0 = get_arg(args, 0)
    x = arg0.ToNumber()

    if isnan(x) or isinf(x):
        return NAN

    if x > 1 or x < -1:
        return NAN

    return math.acos(x)

# 15.8.2.3
def js_asin(this, args):
    arg0 = get_arg(args, 0)
    x = arg0.ToNumber()

    if isnan(x) or isinf(x):
        return NAN

    if x > 1 or x < -1:
        return NAN

    return math.asin(x)

# 15.8.2.4
def js_atan(this, args):
    arg0 = get_arg(args, 0)
    x = arg0.ToNumber()

    if isnan(x):
        return NAN

    if x == INFINITY:
        return math.pi/2

    if x == -INFINITY:
        return -math.pi/2

    return math.atan(x)

# 15.8.2.5
def js_atan2(this, args):
    arg0 = get_arg(args, 0)
    arg1 = get_arg(args, 1)
    y = arg0.ToNumber()
    x = arg1.ToNumber()

    if isnan(x) or isnan(y):
        return NAN

    return math.atan2(y, x)

# 15.8.2.6
def js_ceil(this, args):
    arg0 = get_arg(args, 0)
    x = arg0.ToNumber()

    if isnan(x):
        return NAN

    if x == INFINITY:
        return INFINITY

    if x == -INFINITY:
        return -INFINITY

    return math.ceil(x)

# 15.8.2.7
def js_cos(this, args):
    arg0 = get_arg(args, 0)
    x = arg0.ToNumber()

    if isnan(x) or isinf(x):
        return NAN

    return math.cos(x)

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
