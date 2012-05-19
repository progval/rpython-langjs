def setup(global_object):
    from js.builtins import put_property, put_native_function
    from js.builtins_number import w_NAN
    from js.jsobj import W_DateObject, W_DateConstructor, W__Object
    ##Date
    # 15.9.5

    w_DatePrototype = W_DateObject(w_NAN)
    w_DatePrototype._prototype_ = W__Object._prototype_

    W_DateObject._prototype_ = w_DatePrototype

    # 15.9.5.9
    put_native_function(w_DatePrototype, 'getTime', get_time)

    # 15.9.5.26
    put_native_function(w_DatePrototype, 'getTimezoneOffset', get_timezone_offset)

    # 15.9.3
    w_Date = W_DateConstructor()
    put_property(global_object, 'Date', w_Date)

# 15.9.5.9
def get_time(this, args):
    return this

# 15.9.5.26
def get_timezone_offset(this, args):
    return 0
