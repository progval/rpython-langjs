from js.jsobj import W_Boolean, W_BooleanObject
from js.exception import JsTypeError
from js.object_space import w_return, _w


def setup(global_object):
    from js.builtins import put_property, put_native_function
    from js.object_space import object_space

    # 15.6.2
    from js.jsobj import W_BooleanConstructor
    w_Boolean = W_BooleanConstructor()
    object_space.assign_proto(w_Boolean, object_space.proto_function)
    put_property(global_object, u'Boolean', w_Boolean)

    # 15.6.3
    put_property(w_Boolean, u'length', _w(1), writable=False, enumerable=False, configurable=False)

    # 15.6.4
    w_BooleanPrototype = W_BooleanObject(_w(False))
    object_space.assign_proto(w_BooleanPrototype, object_space.proto_object)

    # 15.6.3.1
    object_space.proto_boolean = w_BooleanPrototype

    # 15.6.3.1
    put_property(w_Boolean, u'prototype', w_BooleanPrototype, writable=False, enumerable=False, configurable=False)

    # 15.6.4.1
    put_property(w_BooleanPrototype, u'constructor', w_Boolean)

    # 15.6.4.2
    put_native_function(w_BooleanPrototype, u'toString', to_string)

    # 15.6.4.3
    put_native_function(w_BooleanPrototype, u'valueOf', value_of)


# 15.6.4.2
@w_return
def to_string(this, args):
    if isinstance(this, W_Boolean):
        b = this
    elif isinstance(this, W_BooleanObject):
        b = this.PrimitiveValue()
    else:
        raise JsTypeError(u'')

    if b.to_boolean() is True:
        return u'true'
    else:
        return u'false'


# 15.6.4.3
@w_return
def value_of(this, args):
    if isinstance(this, W_Boolean):
        b = this
    elif isinstance(this, W_BooleanObject):
        b = this.PrimitiveValue()
    else:
        raise JsTypeError(u'')

    return b
