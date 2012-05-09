class JsBaseExcept(Exception):
    pass

#XXX Just an idea for now
class JsRuntimeExcept(Exception):
    def __init__(self, pos, message, exception_object):
        self.pos = pos
        self.message = message
        self.exception_object = exception_object # JS Exception Object

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class ExecutionReturned(JsBaseExcept):
    def __init__(self, type='normal', value=None, identifier=None):
        self.type = type
        self.value = value
        self.identifier = identifier

class ThrowException(JsBaseExcept):
    def __init__(self, exception):
        self.exception = exception
        self.args = [exception]

class JsException(Exception):
    def __init__(self, value = None):
        from js.jsobj import _w
        self.value = _w(value)

class JsThrowException(JsException):
    pass

class JsTypeError(JsException):
    pass

class JsReferenceError(JsException):
    def __init__(self, identifier):
        s = "ReferenceError: %s is not defined" % (identifier)
        JsException.__init__(self, s)

class JsRangeError(JsException):
    pass

class JsSyntaxError(JsException):
    pass
