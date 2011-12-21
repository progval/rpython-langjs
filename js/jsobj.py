# encoding: utf-8
from pypy.rpython.lltypesystem import rffi
from pypy.rlib.rarithmetic import r_uint, intmask, ovfcheck_float_to_int
from pypy.rlib.rfloat import isnan, isinf, NAN, formatd
from js.execution import ThrowException, JsTypeError, RangeError, ReturnException

from pypy.rlib.jit import hint
from pypy.rlib import jit, debug
from js.utils import StackMixin
from js.object_map import root_map

import string
# see ECMA 8.6.1 Property attributes
DONT_ENUM = DE = 1 # DontEnum
DONT_DELETE = DD = 2 # DontDelete
READ_ONLY = RO = 4 # ReadOnly
INTERNAL = IT = 8 # Internal


class SeePage(NotImplementedError):
    pass

class W___Root(object):
    pass

class W__Root(W___Root):
    _settled_ = True
    _attrs_ = []
    _type_ = ''

    def __str__(self):
        return self.ToString()

    def type(self):
        return self._type_

    def ToBoolean(self):
        return False

    def ToPrimitive(self, hint = None):
        return self

    def ToString(self):
        return ''

    def ToObject(self):
        raise JsTypeError

    def ToNumber(self):
        return 0.0

    def ToInteger(self):
        return int(self.ToNumber())

    def ToInt32(self):
        return r_int32(self.ToInteger())

    def ToUInt32(self):
        return r_uint32(self.ToInteger())

class W_Root(W___Root):
    _settled_ = True
    _attrs_ = []
    def __init__(self):
        pass

    def tolist(self):
        raise JsTypeError('arrayArgs is not an Array or Arguments object')

    def ToBoolean(self):
        raise NotImplementedError(self.__class__)

    def ToPrimitive(self, hint=""):
        return self

    def ToString(self):
        return ''

    def ToObject(self):
        # XXX should raise not implemented
        return self

    def ToNumber(self):
        return 0.0

    def ToInteger(self):
        return int(self.ToNumber())

    def ToInt32(self):
        return r_int32(int(self.ToNumber()))

    def ToUInt32(self):
        return r_uint32(0)

    def Get(self, P):
        raise NotImplementedError(self.__class__)

    def Put(self, P, V, flags = 0):
        raise NotImplementedError(self.__class__)

    def PutValue(self, w):
        pass

    def CanPut(self, P):
        return False

    def Call(self, args=[], this=None):
        raise NotImplementedError(self.__class__)

    def __str__(self):
        return self.ToString()

    def type(self):
        raise NotImplementedError(self.__class__)

    def GetPropertyName(self):
        raise NotImplementedError(self.__class__)

    def HasProperty(self, identifier):
        return False

    def Delete(self, name):
        return False

class W__Primitive(W__Root):
    pass

class W_Undefined(W__Primitive):
    _type_ = 'undefined'
    def ToInteger(self):
        return 0

    def ToNumber(self):
        return NAN

    def ToString(self):
        return self._type_

class W_Null(W__Primitive):
    _type_ = 'null'

    def ToBoolean(self):
        return False

    def ToString(self):
        return self._type_

w_Undefined = W_Undefined()
w_Null = W_Null()

class W_ContextObject(W_Root):
    def __init__(self, ctx):
        self.context = ctx

    def __repr__(self):
        return '<W_ContextObject (%s)>' % (repr(self.context),)

    def Get(self, name):
        try:
            return self.context.get_property_value(name)
        except KeyError:
            from js.jsobj import w_Undefined
            return w_Undefined

    def Put(self, P, V, flags = 0):
        self.context.put(P, V)

    def Delete(self, name):
        try:
            if self.context.get_property_flags(name) & DONT_DELETE:
                return False
            self.context.delete_identifier(name)
        except KeyError:
            pass
        return True

class W_BasicObject(W__Root):
    _immutable_fields_ = ['_class_', '_prototype_', '_primitive_value_']
    _type_ = 'object'
    _class_ = 'Object'
    _prototype_ = w_Undefined

    def __init__(self):
        W__Root.__init__(self)
        self._property_map = root_map()
        self._property_values = []
        self._set_property('prototype', self._prototype_, DONT_ENUM | DONT_DELETE)

    def __repr__(self):
        #keys = self._property_map.keys()
        #values = [str(i) for i in self._property_values], str(dict(zip(keys, values)))
        return "%s: %s" % (object.__repr__(self), self.Class())

    def _set_property(self, name, value, flags):
        if self._property_map.lookup(name) == self._property_map.NOT_FOUND:
            self._property_map = self._property_map.add(name, flags)
        self._set_property_value(name, value)
        self._set_property_flags(name, flags)

    def _set_property_value(self, name, value):
        idx = self._property_map.lookup(name)
        l = len(self._property_values)

        if l <= idx:
            self._property_values = self._property_values + ([None] * (idx - l + 1))

        self._property_values[idx] = value

    def _set_property_flags(self, name, flags):
        self._property_map = self._property_map.set_flags(name, flags)

    def _get_property_value(self, name):
        idx = self._property_map.lookup(name)
        if idx == self._property_map.NOT_FOUND:
            raise KeyError
        return self._property_values[idx]

    def _get_property_keys(self):
        return self._property_map.keys()

    def _get_property_flags(self, name):
        flag = self._property_map.lookup_flag(name)
        if flag == self._property_map.NOT_FOUND:
            raise KeyError
        return flag

    def _has_property(self, name):
        return self._property_map.lookup(name) != self._property_map.NOT_FOUND

    @jit.unroll_safe
    def _delete_property(self, name):
        idx = self._property_map.lookup(name)
        old_map = self._property_map
        new_map = self._property_map.delete(name)
        new_keys = new_map.keys()
        new_values = [None] * len(new_keys)
        old_values = self._property_values

        for key in new_keys:
            old_index = old_map.lookup(key)
            new_index = new_map.lookup(key)
            new_values[new_index] = old_values[old_index]

        self._property_values = new_values
        self._property_map = new_map

    #########

    def Prototype(self):
        return self._prototype_

    def Class(self):
        return self._class_

    def ToBoolean(self):
        return True

    def ToNumber(self):
        return self.ToPrimitive('Number').ToNumber()

    def ToString(self):
        return self.ToPrimitive('String').ToString()

    def ToPrimitive(self, hint = None):
        return self.DefaultValue(hint)

    def ToObject(self):
        return self

    ##########

    def IsCallable(self):
        return False

    def DefaultValue(self, hint = 'Number'):
        props = ['valueOf', 'toString']
        if hint == 'String':
            props = ['toString', 'valueOf']

        for prop in props:
            p = self.Get(prop)
            if isinstance(p, W_BasicObject) and p.IsCallable():
                res = p.Call(this = self)
                if isinstance(res, W__Primitive):
                    return res

        raise JsTypeError

    def Get(self, P):
        try:
            return self._get_property_value(P)
        except KeyError:
            if isnull_or_undefined(self.Prototype()):
                return w_Undefined

        assert self.Prototype() is not self
        return self.Prototype().Get(P) # go down the prototype chain

    def CanPut(self, P):
        if self._has_property(P):
            if self._get_property_flags(P) & READ_ONLY: return False
            return True

        if isnull_or_undefined(self.Prototype()): return True

        assert self.Prototype() is not self
        return self.Prototype().CanPut(P)

    def Put(self, P, V, flags = 0):
        # TODO: ???
        if self._has_property(P):
            self._set_property_value(P, V)
            f = self._get_property_flags(P) | flags
            self._set_property_flags(P, f)
            return

        if not self.CanPut(P): return
        self._set_property(P, V, flags)

    def GetPropertyName(self):
        raise NotImplementedError(self.__class__)

    def HasProperty(self, P):
        if self._has_property(P): return True

        if isnull_or_undefined(self.Prototype()): return False

        assert self.Prototype() is not self
        return self.Prototype().HasProperty(P)

    def Delete(self, P):
        if self._has_property(P):
            if self._get_property_flags(P) & DONT_DELETE:
                return False
            self._delete_property(P)
            return True
        return True

class W__PrimitiveObject(W_BasicObject):
    def __init__(self, primitive_value):
        W_BasicObject.__init__(self)
        self._primitive_value_ = _w(primitive_value)

    def PrimitiveValue(self):
        return self._primitive_value_

    def ToString(self):
        return self.PrimitiveValue().ToString()

class W_BooleanObject(W__PrimitiveObject):
    _class_ = 'Boolean'

    def ToString(self):
        return self.PrimitiveValue().ToString()

class W_NumericObject(W__PrimitiveObject):
    _class_ = 'Number'

class W_StringObject(W__PrimitiveObject):
    _class_ = 'String'

class W__Object(W_BasicObject):
    def ToString(self):
        try:
            res = self.ToPrimitive('String')
        except JsTypeError:
            return "[object %s]" % (self.Class() ,)
        return res.ToString()

class W_ObjectConstructor(W_BasicObject):
    def __init__(self):
        W_BasicObject.__init__(self)

    def ToString(self):
        return "function Object() { [native code] }"

    def IsCallable(self):
        return True

    def Call(self, args=[], this=None):
        return self.Construct(args)

    def Construct(self, args=[]):
        if len(args) >= 1 and not isnull_or_undefined(args[0]):
            return args[0].ToObject()

        obj = W__Object()
        return obj

class W_BasicFunction(W_BasicObject):
    _class_ = 'Function'
    _type_ = 'function'
    _immutable_fields_ = ['_context_']

    def __init__(self, context):
        W_BasicObject.__init__(self)
        self._context_ = context

    def Call(self, args=[], this=None):
        raise NotImplementedError(self.__class__)

    # 13.2.2
    def Construct(self, args=[]):
        obj = W__Object()
        proto = self.Get('prototype')
        if isinstance(proto, W_BasicObject) or isinstance(proto, W_PrimitiveObject):
            obj._prototype_ = proto
        else:
            # would love to test this
            # but I fail to find a case that falls into this
            obj._prototype_ = W__Object._prototype_


        try: #this is a hack to be compatible to spidermonkey
            self.Call(args, this=obj)
        except ReturnException, e:
            result = e.value
            if isinstance(result, W_BasicObject) or isinstance(result, W_PrimitiveObject):
                return result
        return obj

    def IsCallable(self):
        return True

class W_FunctionConstructor(W_BasicFunction):
    def __init__(self, ctx):
        W_BasicFunction.__init__(self, ctx)

    def ToString(self):
        return "function Function() { [native code] }"

    def Call(self, args=[], this=None):
        from js.jsparser import parse
        from js.jscode import JsCode
        from js.astbuilder import make_ast_builder

        # 15.3.2.1
        functioncode = "function () { }"
        tam = len(args)
        if tam >= 1:
            fbody  = args[tam-1].ToString()
            argslist = []
            for i in range(tam-1):
                argslist.append(args[i].ToString())
            fargs = ','.join(argslist)
            functioncode = "return function (%s) {%s}"%(fargs, fbody)
        #remove program and sourcelements node
        funcnode = parse(functioncode).children[0].children[0]
        builder = make_ast_builder()
        ast = builder.dispatch(funcnode)
        bytecode = JsCode()
        ast.emit(bytecode)
        func = bytecode.make_js_function()
        func2 = func.run(self._context_)
        return func2

    # TODO
    def Construct(self, args=[]):
        return self.Call(args, this=None)

# 15.7.2
class W_NumberConstructor(W_BasicFunction):
    # 15.7.1.1
    def Call(self, args=[], this=None):
        if len(args) >= 1 and not isnull_or_undefined(args[0]):
            return _w(args[0].ToNumber())
        elif len(args) >= 1 and args[0] is w_Undefined:
            return _w(NAN)
        else:
            return _w(0.0)

    # 15.7.2.1
    def Construct(self, args=[]):
        return self.Call(args).ToObject()

# 15.5.2
class W_StringConstructor(W_BasicFunction):
    def Call(self, args=[], this=None):
        assert False
        return w_Undefined

    def Construct(self, args=[]):
        return self.Call(args).ToObject()

# 15.6.2
class W_BooleanConstructor(W_BasicFunction):
    def Call(self, args=[], this=None):
        if len(args) >= 1 and not isnull_or_undefined(args[0]):
            return _w(args[0].ToBoolean())
        else:
            return _w(False)

    def Construct(self, args=[]):
        return self.Call(args).ToObject()

class W__Function(W_BasicFunction):
    _immutable_fields_ = ['_function_']

    def __init__(self, context, function):
        W_BasicFunction.__init__(self, context)
        self._function_ = function

    def Call(self, args=[], this=None):
        result = self._function_.run(self._context_, args, this)
        return result

    def ToString(self):
        return self._function_.ToString()

class W_Arguments(W_BasicObject):
    def tolist(self):
        l = []
        for i in range(self.length):
            l.append(self._get_property_value(str(i)))
        return l

    @jit.unroll_safe
    def __init__(self, callee, args):
        W_BasicObject.__init__(self)
        self._delete_property('prototype')
        self.Put('callee', callee)
        self.Put('length', W_IntNumber(len(args)))
        for i in range(len(args)):
            self.Put(str(i), args[i])
        self.length = len(args)

class W_ArrayConstructor(W_BasicObject):
    def IsCallable(self):
        return True

    def Call(self, args=[], this=None):
        if len(args) == 1 and isinstance(args[0], W_Number):
            array = W__Array()
        else:
            array = W__Array()
            for index, obj in enumerate(args):
                array.Put(str(index), obj)
        return array

    def Construct(self, args=[]):
        return self.Call(args)

class W__Array(W_BasicObject):
    _class_ = 'Array'
    length = r_uint(0)

    def __init__(self):
        W_BasicObject.__init__(self)
        self.Put('length', _w(0), flags = DONT_DELETE)

    def set_length(self, newlength):
        if newlength < self.length:
            i = newlength
            while i < self.length:
                key = str(i)
                if key in self._get_property_keys():
                    self._delete_property(key)
                i += 1

        self.length = int(newlength)
        self._set_property_value('length', _w(self.length))

    def Put(self, P, V, flags = 0):
        if not self.CanPut(P): return
        if not self._has_property(P):
            self._set_property(P,V,flags)
        else:
            if P != 'length':
                self._set_property_value(P, V)
            else:
                length = V.ToUInt32()
                if length != V.ToNumber():
                    raise RangeError()

                self.set_length(length)
                return

        try:
            arrayindex = r_uint(to_array_index(P))
        except ValueError:
            return

        if (arrayindex < self.length) or (arrayindex != float(P)):
            return
        else:
            if (arrayindex + 1) == 0:
                raise RangeError()
            self.set_length(arrayindex+1)

# 15.8
class W_Math(W__Object):
    _class_ = 'Math'

class W_Boolean(W__Primitive):
    _immutable_fields_ = ['_boolval_']
    _type_ = 'boolean'

    def __init__(self, boolval):
        W__Primitive.__init__(self)
        self._boolval_ = bool(boolval)

    def __repr__(self):
        return 'W_Bool(%s)' % (str(self._boolval_), )

    def ToObject(self):
        return W_BooleanObject(self)

    def ToString(self):
        if self._boolval_ == True:
            return "true"
        return "false"

    def ToNumber(self):
        if self._boolval_ == True:
            return 1.0
        return 0.0

    def ToBoolean(self):
        return self._boolval_

class W_String(W__Primitive):
    _immutable_fields_ = ['_strval_']
    _type_ = 'string'

    def __init__(self, strval):
        W__Primitive.__init__(self)
        self._strval_ = strval

    def __repr__(self):
        return 'W_String(%s)' % (repr(self._strval_),)

    def ToObject(self):
        return W_StringObject(self)

    def ToString(self):
        return self._strval_

    def ToBoolean(self):
        if len(self._strval_) == 0:
            return False
        else:
            return True

    def ToNumber(self):
        if not self._strval_:
            return 0.0
        try:
            return float(self._strval_)
        except ValueError:
            try:
                return float(int(self._strval_, 16))
            except ValueError:
                try:
                    return float(int(self._strval_, 8))
                except ValueError:
                    return NAN

class W_Number(W__Primitive):
    """ Base class for numbers, both known to be floats
    and those known to be integers
    """
    _type_ = 'number'

    # 9.9
    def ToObject(self):
        return W_NumericObject(self)

    def ToBoolean(self):
        num = self.ToNumber()
        if isnan(num):
            return False
        return bool(num)

class W_IntNumber(W_Number):
    _immutable_fields_ = ['_intval_']
    """ Number known to be an integer
    """
    def __init__(self, intval):
        W_Number.__init__(self)
        self._intval_ = intmask(intval)

    def __repr__(self):
        return 'W_IntNumber(%s)' % (self._intval_,)

    def ToInteger(self):
        return self._intval_

    def ToNumber(self):
        # XXX
        return float(self._intval_)

    def ToString(self):
        # XXX incomplete, this doesn't follow the 9.8.1 recommendation
        return str(self.ToInteger())

def r_int32(n):
    return intmask(rffi.cast(rffi.INT, n))

def r_uint32(n):
    return intmask(rffi.cast(rffi.UINT, n))

class W_FloatNumber(W_Number):
    _immutable_fields_ = ['_floatval_']
    """ Number known to be a float
    """
    def __init__(self, floatval):
        W_Number.__init__(self)
        self._floatval_ = float(floatval)

    def __repr__(self):
        return 'W_FloatNumber(%s)' % (self._floatval_,)

    def ToString(self):
        # XXX incomplete, this doesn't follow the 9.8.1 recommendation
        if isnan(self._floatval_):
            return 'NaN'
        if isinf(self._floatval_):
            if self._floatval_ > 0:
                return 'Infinity'
            else:
                return '-Infinity'
        res = ''
        try:
            res = formatd(self._floatval_, 'g', 10)
        except OverflowError:
            raise

        if len(res) > 3 and (res[-3] == '+' or res[-3] == '-') and res[-2] == '0':
            cut = len(res) - 2
            assert cut >= 0
            res = res[:cut] + res[-1]
        return res

    def ToNumber(self):
        return self._floatval_

    def ToInteger(self):
        if isnan(self._floatval_):
            return 0

        if self._floatval_ == 0 or isinf(self._floatval_):
            return self._floatval_

        return intmask(int(self._floatval_))

class W_List(W_Root):
    def __init__(self, list_w):
        self.list_w = list_w

    def ToString(self):
        raise SeePage(42)

    def ToBoolean(self):
        return bool(self.list_w)

    def get_args(self):
        return self.list_w

    def tolist(self):
        return self.list_w

    def __repr__(self):
        return 'W_List(%s)' % (self.list_w,)

class W_Iterator(W_Root):
    def __init__(self, elements_w):
        self.elements_w = elements_w

    def next(self):
        if self.elements_w:
            return self.elements_w.pop()

    def empty(self):
        return len(self.elements_w) == 0

def isnull_or_undefined(obj):
    if obj is w_Null or obj is w_Undefined:
        return True
    return False

def to_array_index(s):
    '''Convert s to an integer if (and only if) s is a valid array index.
    ValueError is raised if conversion is not possible.
    '''
    length = len(s)

    if length == 0 or length > 10: # len(str(2 ** 32))
        raise ValueError

    # '0' is only valid if no characters follow it
    if s[0] == '0':
        if length == 1:
            return 0
        else:
            raise ValueError

    arrayindex = 0
    for i in range(length):
        if s[i] not in string.digits:
            raise ValueError
        arrayindex = (arrayindex * 10) + (ord(s[i]) - ord('0'))
        #XXX: check for overflow?
    return arrayindex

w_True = W_Boolean(True)
w_False = W_Boolean(False)

def newbool(val):
    if val:
        return w_True
    return w_False

def _w(value):
    if isinstance(value, W___Root):
        return value
    elif isinstance(value, bool):
        return newbool(value)
    elif isinstance(value, int):
        return W_IntNumber(value)
    elif isinstance(value, float):
        return W_FloatNumber(value)
    elif isinstance(value, str):
        return W_String(value)
    elif value is None:
        return w_Null
    raise TypeError(value)
