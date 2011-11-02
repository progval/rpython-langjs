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

class W_Root(object):
    _settled_ = True
    _attrs_ = []
    def __init__(self):
        pass

    def tolist(self):
        raise JsTypeError('arrayArgs is not an Array or Arguments object')

    def ToBoolean(self):
        raise NotImplementedError(self.__class__)

    def ToPrimitive(self, ctx, hint=""):
        return self

    def ToString(self, ctx):
        return ''

    def ToObject(self, ctx):
        # XXX should raise not implemented
        return self

    def ToNumber(self, ctx = None):
        return 0.0

    def ToInteger(self, ctx):
        return int(self.ToNumber(ctx = None))

    def ToInt32(self):
        return r_int32(int(self.ToNumber()))

    def ToUInt32(self):
        return r_uint32(0)

    def Get(self, P):
        raise NotImplementedError(self.__class__)

    def Put(self, P, V, flags = 0):
        raise NotImplementedError(self.__class__)

    def PutValue(self, w, ctx):
        pass

    def CanPut(self, P):
        return False

    def Call(self, ctx, args=[], this=None):
        raise NotImplementedError(self.__class__)

    def __str__(self):
        return self.ToString(ctx=None)

    def type(self):
        raise NotImplementedError(self.__class__)

    def GetPropertyName(self):
        raise NotImplementedError(self.__class__)

    def HasProperty(self, identifier):
        return False

    def Delete(self, name):
        return False

class W_Undefined(W_Root):
    def __str__(self):
        return "w_undefined"

    def ToInteger(self, ctx):
        return 0

    def ToNumber(self, ctx = None):
        return NAN

    def ToBoolean(self):
        return False

    def ToString(self, ctx):
        return "undefined"

    def type(self):
        return 'undefined'

    def tolist(self):
        return []

class W_Null(W_Root):
    def __str__(self):
        return "null"

    def ToBoolean(self):
        return False

    def ToString(self, ctx):
        return "null"

    def type(self):
        return 'null'

    def tolist(self):
        return []

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

class W_PrimitiveObject(W_Root):
    _immutable_fields_ = ['Class', 'Property', 'Scope', 'Value']
    def __init__(self, ctx=None, Prototype=None, Class='Object', Value=w_Undefined):
        self.Prototype = Prototype
        self.property_map = root_map()
        self.property_values = []
        if Prototype is None:
            Prototype = w_Undefined
        self._set_property('prototype', Prototype, DONT_ENUM | DONT_DELETE)
        self.Class = Class
        self.Scope = None
        self.Value = Value

    def _set_property(self, name, value, flags):
        if self.property_map.lookup(name) == self.property_map.NOT_FOUND:
            self.property_map = self.property_map.add(name, flags)
        self._set_property_value(name, value)
        self._set_property_flags(name, flags)

    def _set_property_value(self, name, value):
        idx = self.property_map.lookup(name)
        l = len(self.property_values)

        if l <= idx:
            self.property_values = self.property_values + ([None] * (idx - l + 1))

        self.property_values[idx] = value

    def _set_property_flags(self, name, flags):
        self.property_map = self.property_map.set_flags(name, flags)

    def _get_property_value(self, name):
        idx = self.property_map.lookup(name)
        if idx == self.property_map.NOT_FOUND:
            raise KeyError
        return self.property_values[idx]

    def _get_property_flags(self, name):
        flag = self.property_map.lookup_flag(name)
        if flag == self.property_map.NOT_FOUND:
            raise KeyError
        return flag

    def _has_property(self, name):
        return self.property_map.lookup(name) != self.property_map.NOT_FOUND

    @jit.unroll_safe
    def _delete_property(self, name):
        idx = self.property_map.lookup(name)
        old_map = self.property_map
        new_map = self.property_map.delete(name)
        new_keys = new_map.keys()
        new_values = [None] * len(new_keys)
        old_values = self.property_values

        for key in new_keys:
            old_index = old_map.lookup(key)
            new_index = new_map.lookup(key)
            new_values[new_index] = old_values[old_index]

        self.property_values = new_values
        self.property_map = new_map

    def _get_property_keys(self):
        return self.property_map.keys()

    def Call(self, ctx, args=[], this=None):
        raise JsTypeError('not a function')

    def Construct(self, ctx, args=[]):
        obj = W_Object(Class='Object')
        prot = self.Get('prototype')
        if isinstance(prot, W_PrimitiveObject):
            obj.Prototype = prot
        else: # would love to test this
            #but I fail to find a case that falls into this
            obj.Prototype = ctx.get_global().Get('Object').Get('prototype')
        try: #this is a hack to be compatible to spidermonkey
            self.Call(ctx, args, this=obj)
            return obj
        except ReturnException, e:
            return e.value

    def Get(self, P):
        try:
            return self._get_property_value(P)
        except KeyError:
            if self.Prototype is None:
                return w_Undefined
        return self.Prototype.Get(P) # go down the prototype chain

    def CanPut(self, P):
        if self._has_property(P):
            if self._get_property_flags(P) & READ_ONLY: return False
            return True
        if self.Prototype is None: return True
        return self.Prototype.CanPut(P)

    def Put(self, P, V, flags = 0):
        if self._has_property(P):
            self._set_property_value(P, V)
            f = self._get_property_flags(P) | flags
            self._set_property_flags(P, f)
            return

        if not self.CanPut(P): return
        self._set_property(P, V, flags)

    def HasProperty(self, P):
        if self._has_property(P): return True
        if self.Prototype is None: return False
        return self.Prototype.HasProperty(P)

    def Delete(self, P):
        if self._has_property(P):
            if self._get_property_flags(P) & DONT_DELETE:
                return False
            self._delete_property(P)
            return True
        return True

    def internal_def_value(self, ctx, tryone, trytwo):
        t1 = self.Get(tryone)
        if isinstance(t1, W_PrimitiveObject):
            val = t1.Call(ctx, this=self)
            if isinstance(val, W_Primitive):
                return val
        t2 = self.Get(trytwo)
        if isinstance(t2, W_PrimitiveObject):
            val = t2.Call(ctx, this=self)
            if isinstance(val, W_Primitive):
                return val
        raise JsTypeError

    def DefaultValue(self, ctx, hint=""):
        if hint == "String":
            return self.internal_def_value(ctx, "toString", "valueOf")
        else: # hint can only be empty, String or Number
            return self.internal_def_value(ctx, "valueOf", "toString")

    ToPrimitive = DefaultValue

    def ToBoolean(self):
        return True

    def ToString(self, ctx):
        try:
            res = self.ToPrimitive(ctx, 'String')
        except JsTypeError:
            return "[object %s]"%(self.Class,)
        return res.ToString(ctx)

    def __str__(self):
        return "<Object class: %s>" % self.Class

    def type(self):
        return 'object'

def str_builtin(ctx, args, this):
    return W_String(this.ToString(ctx))

class W_Object(W_PrimitiveObject):
    def __init__(self, ctx=None, Prototype=None, Class='Object', Value=w_Undefined):
        W_PrimitiveObject.__init__(self, ctx, Prototype, Class, Value)

    def ToNumber(self, ctx = None):
        return self.Get('valueOf').Call(ctx, args=[], this=self).ToNumber(ctx)

class W_CallableObject(W_Object):
    _immutable_fields_ = ['callfunc', 'ctx']
    def __init__(self, ctx, Prototype, callfunc):
        W_Object.__init__(self, ctx, Prototype, 'Function')
        self.ctx = ctx
        self.callfunc = callfunc

    @jit.unroll_safe
    def Call(self, ctx, args=[], this=None):
        # TODO
        if this:
            from js.jsobj import W_Root
            assert isinstance(this, W_Root)

        from js.jsexecution_context import make_activation_context, make_function_context

        w_Arguments = W_Arguments(self, args)
        act = make_activation_context(self.ctx, this, w_Arguments)
        newctx = make_function_context(act, self.callfunc)

        paramn = len(self.callfunc.params)
        for i in range(paramn):
            paramname = self.callfunc.params[i]
            try:
                value = args[i]
            except IndexError:
                value = w_Undefined
            newctx.declare_variable(paramname)
            newctx.assign(paramname, value)

        val = self.callfunc.run(ctx=newctx)
        return val

    def type(self):
        return 'function'

class W_Primitive(W_Root):
    """unifying parent for primitives"""
    def ToPrimitive(self, ctx, hint=""):
        return self


class W_NewBuiltin(W_PrimitiveObject):
    length = -1
    def __init__(self, ctx, Prototype=None, Class='function', Value=w_Undefined):
        if Prototype is None:
            proto = ctx.get_global().Get('Function').Get('prototype')
            Prototype = proto

        W_PrimitiveObject.__init__(self, ctx, Prototype, Class, Value)

        if self.length != -1:
            self.Put('length', W_IntNumber(self.length), flags = DONT_ENUM|DONT_DELETE|READ_ONLY)


    def Call(self, ctx, args=[], this = None):
        raise NotImplementedError

    def type(self):
        return self.Class

class W_Builtin(W_PrimitiveObject):
    def __init__(self, builtin=None, ctx=None, Prototype=None, Class='function', Value=w_Undefined):
        W_PrimitiveObject.__init__(self, ctx, Prototype, Class, Value)
        self.set_builtin_call(builtin)

    def set_builtin_call(self, callfuncbi):
        self.callfuncbi = callfuncbi

    def Call(self, ctx, args=[], this = None):
        return self.callfuncbi(ctx, args, this)

    def Construct(self, ctx, args=[]):
        return self.callfuncbi(ctx, args, None)

    def type(self):
        return self.Class

class W_ListObject(W_PrimitiveObject):
    def tolist(self):
        l = []
        for i in range(self.length):
            l.append(self._get_property_value(str(i)))
        return l

class W_Arguments(W_ListObject):
    @jit.unroll_safe
    def __init__(self, callee, args):
        W_PrimitiveObject.__init__(self, Class='Arguments')
        self._delete_property('prototype')
        self.Put('callee', callee)
        self.Put('length', W_IntNumber(len(args)))
        for i in range(len(args)):
            self.Put(str(i), args[i])
        self.length = len(args)

class ActivationObject(W_PrimitiveObject):
    """The object used on function calls to hold arguments and this"""
    def __init__(self):
        W_PrimitiveObject.__init__(self, Class='Activation')
        self._delete_property('prototype')

    def __repr__(self):
        return str(self.property_map)

class W_Array(W_ListObject):
    def __init__(self, ctx=None, Prototype=None, Class='Array', Value=w_Undefined):
        W_ListObject.__init__(self, ctx, Prototype, Class, Value)
        self.Put('length', W_IntNumber(0), flags = DONT_DELETE)
        self.length = r_uint(0)

    def set_length(self, newlength):
        if newlength < self.length:
            i = newlength
            while i < self.length:
                key = str(i)
                if key in self._get_property_keys():
                    self._delete_property(key)
                i += 1

        self.length = newlength
        self._set_property_value('length', W_FloatNumber(newlength))

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

class W_Boolean(W_Primitive):
    _immutable_fields_ = ['boolval']
    def __init__(self, boolval):
        self.boolval = bool(boolval)

    def ToObject(self, ctx):
        return create_object(ctx, 'Boolean', Value=self)

    def ToString(self, ctx=None):
        if self.boolval == True:
            return "true"
        return "false"

    def ToNumber(self, ctx = None):
        if self.boolval:
            return 1.0
        return 0.0

    def ToBoolean(self):
        return self.boolval

    def type(self):
        return 'boolean'

    def __repr__(self):
        return "<W_Bool "+str(self.boolval)+" >"

class W_String(W_Primitive):
    _immutable_fields_ = ['strval']
    def __init__(self, strval):
        W_Primitive.__init__(self)
        self.strval = strval

    def __repr__(self):
        return 'W_String(%s)' % (self.strval,)

    def ToObject(self, ctx):
        o = create_object(ctx, 'String', Value=self)
        o.Put('length', W_IntNumber(len(self.strval)), flags = READ_ONLY | DONT_DELETE | DONT_ENUM)
        return o

    def ToString(self, ctx=None):
        return self.strval

    def ToBoolean(self):
        if len(self.strval) == 0:
            return False
        else:
            return True

    def type(self):
        return 'string'

    def GetPropertyName(self):
        return self.ToString()

    def ToNumber(self, ctx = None):
        if not self.strval:
            return 0.0
        try:
            return float(self.strval)
        except ValueError:
            try:
                return float(int(self.strval, 16))
            except ValueError:
                try:
                    return float(int(self.strval, 8))
                except ValueError:
                    return NAN


class W_BaseNumber(W_Primitive):
    """ Base class for numbers, both known to be floats
    and those known to be integers
    """
    def ToObject(self, ctx):
        return create_object(ctx, 'Number', Value=self)

    def Get(self, P):
        return w_Undefined

    def type(self):
        return 'number'

class W_IntNumber(W_BaseNumber):
    _immutable_fields_ = ['intval']
    """ Number known to be an integer
    """
    def __init__(self, intval):
        W_BaseNumber.__init__(self)
        self.intval = intmask(intval)

    def ToString(self, ctx=None):
        # XXX incomplete, this doesn't follow the 9.8.1 recommendation
        return str(self.intval)

    def ToBoolean(self):
        return bool(self.intval)

    def ToNumber(self, ctx = None):
        # XXX
        return float(self.intval)

    def ToInt32(self):
        return r_int32(self.intval)

    def ToUInt32(self):
        return r_uint32(self.intval)

    def GetPropertyName(self):
        return self.ToString()

    def __repr__(self):
        return 'W_IntNumber(%s)' % (self.intval,)

def r_int32(n):
    return intmask(rffi.cast(rffi.INT, n))

def r_uint32(n):
    return intmask(rffi.cast(rffi.UINT, n))

class W_FloatNumber(W_BaseNumber):
    _immutable_fields_ = ['floatval']
    """ Number known to be a float
    """
    def __init__(self, floatval):
        W_BaseNumber.__init__(self)
        self.floatval = float(floatval)

    def ToString(self, ctx = None):
        # XXX incomplete, this doesn't follow the 9.8.1 recommendation
        if isnan(self.floatval):
            return 'NaN'
        if isinf(self.floatval):
            if self.floatval > 0:
                return 'Infinity'
            else:
                return '-Infinity'
        res = ''
        try:
            res = formatd(self.floatval, 'g', 10)
        except OverflowError:
            raise

        if len(res) > 3 and (res[-3] == '+' or res[-3] == '-') and res[-2] == '0':
            cut = len(res) - 2
            assert cut >= 0
            res = res[:cut] + res[-1]
        return res

    def ToBoolean(self):
        if isnan(self.floatval):
            return False
        return bool(self.floatval)

    def ToNumber(self, ctx = None):
        return self.floatval

    def ToInteger(self, ctx):
        if isnan(self.floatval):
            return 0

        if self.floatval == 0 or isinf(self.floatval):
            return self.floatval

        return intmask(int(self.floatval))

    def ToInt32(self):
        if isnan(self.floatval) or isinf(self.floatval):
            return 0
        return r_int32(int(self.floatval))

    def ToUInt32(self):
        if isnan(self.floatval) or isinf(self.floatval):
            return r_uint(0)
        return r_uint32(int(self.floatval))

    def __repr__(self):
        return 'W_FloatNumber(%s)' % (self.floatval,)

class W_List(W_Root):
    def __init__(self, list_w):
        self.list_w = list_w

    def ToString(self, ctx = None):
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

def create_object(ctx, prototypename, Value=w_Undefined):
    proto = ctx.get_global().Get(prototypename).Get('prototype')
    # TODO get Object prototype from interp.w_Object
    assert isinstance(proto, W_PrimitiveObject)
    obj = W_Object(ctx, Prototype=proto, Class = proto.Class, Value = Value)
    obj.Put('__proto__', proto, DONT_ENUM | DONT_DELETE | READ_ONLY)
    return obj

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
