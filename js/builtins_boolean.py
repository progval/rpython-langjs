from js.jsobj import W_Boolean, W_BooleanObject
from js.execution import JsTypeError

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

def value_of(this, args):
    if isinstance(this, W_Boolean):
        b = this
    elif isinstance(this, W_BooleanObject):
        b = this.PrimitiveValue()
    else:
        raise JsTypeError()

    return this.ToBoolean()
