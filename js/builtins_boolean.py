from js.jsobj import W_Boolean, W_BooleanObject
from js.execution import JsTypeError
from js.jsobj import _w

def setup(global_object):
    from js.builtins import put_property, put_native_function
    from js.object_space import object_space

    # 15.6.2
    from js.jsobj import W_BooleanConstructor
    w_Boolean = W_BooleanConstructor()
    put_property(global_object, u'Boolean', w_Boolean)

    # 15.6.3
    put_property(w_Boolean, u'length', _w(1), writable = False, enumerable = False, configurable = False)

    # 15.6.4
    w_BooleanPrototype = object_space.new_obj_with_proto(W_BooleanObject, object_space.proto_object, _w(False))

    # 15.6.3.1
    object_space.proto_boolean = w_BooleanPrototype

    # 15.6.3.1
    put_property(w_Boolean, u'prototype', w_BooleanPrototype, writable = False, enumerable = False, configurable = False)

    # 15.6.4.1
    put_property(w_BooleanPrototype, u'constructor', w_Boolean)

    # 15.6.4.2
    put_native_function(w_BooleanPrototype, u'toString', to_string)

    # 15.6.4.3
    put_native_function(w_BooleanPrototype, u'valueOf', value_of)

# 15.6.4.2
def to_string(this, args):
    if isinstance(this, W_Boolean):
        b = this
    elif isinstance(this, W_BooleanObject):
        b = this.PrimitiveValue()
    else:
        raise JsTypeError(u'')

    if b.to_boolean() == True:
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
        raise JsTypeError(u'')

    return b
