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
    def _msg(self):
        return 'Exception'

    def msg(self):
        from js.jsobj import _w
        return _w(self._msg())

class JsThrowException(JsException):
    def __init__(self, value = None):
        JsException.__init__(self)
        self.value = _w(value)

class JsTypeError(JsException):
    def __init__(self, value = None):
        JsException.__init__(self)
        self.value = value

    def _msg(self):
        return 'TypeError: %s' % (self.value)

class JsReferenceError(JsException):
    def __init__(self, identifier):
        JsException.__init__(self)
        self.identifier = identifier

    def _msg(self):
        return 'ReferenceError: %s' % (self.identifier)

class JsRangeError(JsException):
    def __init__(self, value = None):
        JsException.__init__(self)
        self.value = value

    def _msg(self):
        return 'RangeError: %s' %(str(self.value))

class JsSyntaxError(JsException):
    def __init__(self, msg = '', src = '', line = 0, column = 0):
        JsException.__init__(self)
        self.error_msg = msg
        self.src = src
        self.line = line
        self.column = column

    def _msg(self):
        error_src = self.src.encode('unicode_escape')
        if self.error_msg:
            return 'SyntaxError: "%s" in "%s" at line:%d, column:%d' %(self.error_msg, error_src, self.line, self.column)
        else:
            return 'SyntaxError: in "%s" at line:%d, column:%d' %(error_src, self.line, self.column)
