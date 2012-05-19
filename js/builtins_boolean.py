from js.jsobj import W_Boolean, W_BooleanObject
from js.execution import JsTypeError
from js.jsobj import _w

def setup(global_object):
    from js.builtins import put_property, put_native_function

    # 15.6.2
    from js.jsobj import W_BooleanConstructor
    w_Boolean = W_BooleanConstructor()
    put_property(global_object, 'Boolean', w_Boolean)

    # 15.6.3
    put_property(w_Boolean, 'length', _w(1), writable = False, enumerable = False, configurable = False)

    # 15.6.4
    w_BooleanPrototype = W_BooleanObject(False)

    from js.jsobj import W__Object
    w_BooleanPrototype._prototype_ = W__Object._prototype_
    del(w_BooleanPrototype._properties_['__proto__'])
    put_property(w_BooleanPrototype, '__proto__', w_BooleanPrototype._prototype_, writable = False, enumerable = False, configurable = False)

    # 15.6.3.1
    put_property(w_Boolean, 'prototype', w_BooleanPrototype, writable = False, enumerable = False, configurable = False)

    # 15.6.4.1
    put_property(w_BooleanPrototype, 'constructor', w_Boolean)

    # 15.6.4.2
    put_native_function(w_BooleanPrototype, 'toString', to_string)

    # 15.6.4.3
    put_native_function(w_BooleanPrototype, 'valueOf', value_of)

    # 15.6.3.1
    W_BooleanObject._prototype_ = w_BooleanPrototype

# 15.6.4.2
def to_string(this, args):
    if isinstance(this, W_Boolean):
        b = this
    elif isinstance(this, W_BooleanObject):
        b = this.PrimitiveValue()
    else:
        raise JsTypeError()

    if b.ToBoolean() == True:
        return 'true'
    else:
        return 'false'

# 15.6.4.3
def value_of(this, args):
    if isinstance(this, W_Boolean):
        b = this
    elif isinstance(this, W_BooleanObject):
        b = this.PrimitiveValue()
    else:
        raise JsTypeError()

    return this.ToBoolean()
