class JsBaseExcept(Exception):
    pass


#XXX Just an idea for now
class JsRuntimeExcept(Exception):
    def __init__(self, pos, message, exception_object):
        self.pos = pos
        self.message = message
        self.exception_object = exception_object  # JS Exception Object


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
    message = u'Exception'

    def __init__(self, message=None):
        if message is not None:
            assert isinstance(message, unicode)
            self.message = message

    def _msg(self):
        return self.message

    def msg(self):
        from js.object_space import _w
        return _w(self._msg())


class JsThrowException(JsException):
    def __init__(self, value):
        from js.jsobj import W_Root
        assert isinstance(value, W_Root)
        self.value = value

    def _msg(self):
        s = self.value.to_string()
        return s


class JsTypeError(JsException):
    def __init__(self, value):
        #assert isinstance(value, unicode)
        self.value = value

    def _msg(self):
        return u'TypeError: ' + self.value  # % (self.value, )


class JsReferenceError(JsException):
    def __init__(self, identifier):
        self.identifier = identifier

    def _msg(self):
        return u'ReferenceError: ' + self.identifier + u' is not defined'


class JsRangeError(JsException):
    def __init__(self, value=None):
        self.value = value

    def _msg(self):
        return u'RangeError: %s'  # % (self.value, )


class JsSyntaxError(JsException):
    def __init__(self, msg=u'', src=u'', line=0, column=0):
        self.error_msg = msg
        self.src = src
        self.line = line
        self.column = column

    def _msg(self):
        #error_src = self.src #self.src.encode('unicode_escape')
        if self.error_msg:
            return u'SyntaxError: "%s" in "%s" at line:%d, column:%d'  # %(self.error_msg, error_src, self.line, self.column)
        else:
            return u'SyntaxError: in "%s" at line:%d, column:%d'  # %(error_src, self.line, self.column)
