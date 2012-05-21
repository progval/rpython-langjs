# encoding: utf-8
from pypy.rpython.lltypesystem import rffi
from pypy.rlib.rarithmetic import r_uint, intmask, ovfcheck_float_to_int
from pypy.rlib.rfloat import isnan, isinf, NAN, formatd, INFINITY
from js.execution import JsTypeError, JsRangeError, ReturnException

class W_Root(object):
    _type_ = ''

    def __str__(self):
        return self.to_string()

    def to_string(self):
        return ''

    def type(self):
        return self._type_

    def ToBoolean(self):
        return False

    def ToPrimitive(self, hint = None):
        return self

    def ToObject(self):
        raise JsTypeError()

    def ToNumber(self):
        return 0.0

    def ToInteger(self):
        num = self.ToNumber()
        if num == NAN:
            return 0
        if num == INFINITY or num == -INFINITY:
            return num

        return int(num)

    def ToInt32(self):
        num = self.ToInteger()
        if num == NAN or num == INFINITY or num == -INFINITY:
            return 0

        return r_int32(num)

    def ToUInt32(self):
        num = self.ToInteger()
        if num == NAN or num == INFINITY or num == -INFINITY:
            return 0
        return r_uint32(num)

    def ToInt16(self):
        def sign(i):
            if i > 0:
                return 1
            if i < 0:
                return -1
            return 0

        num = self.ToInteger()
        if num == NAN or num == INFINITY or num == -INFINITY:
            return 0

        import math
        pos_int = sign(num) * math.floor(abs(num))
        int_16_bit = pos_int % math.pow(2, 16)
        return int(int_16_bit)

    def is_callable(self):
        return False

    def check_object_coercible(self):
        pass

class W_Primitive(W_Root):
    pass

class W_Undefined(W_Primitive):
    _type_ = 'undefined'
    def ToInteger(self):
        return 0

    def ToNumber(self):
        return NAN

    def to_string(self):
        return self._type_

    def check_object_coercible(self):
        raise JsTypeError()

class W_Null(W_Primitive):
    _type_ = 'null'

    def ToBoolean(self):
        return False

    def to_string(self):
        return self._type_

    def check_object_coercible(self):
        raise JsTypeError()

w_Undefined = W_Undefined()
w_Null = W_Null()

# 8.6.1
class Property(object):
    value = w_Undefined
    getter = w_Undefined
    setter = w_Undefined
    writable = False
    enumerable = False
    configurable = False

    def __init__(self, value = None, writable = None, getter = None, setter = None, enumerable = None, configurable = None):
        if value is not None:
            self.value = value
        if writable is not None:
            self.writable = writable
        if getter is not None:
            self.getter = getter
        if setter is not None:
            self.setter = setter
        if enumerable is not None:
            self.enumerable = enumerable
        if configurable is not None:
            self.configurable = configurable

    def is_data_property(self):
        return False

    def is_accessor_property(self):
        return False

    def update_with(self, other):
        if other.value is not None:
            self.value = other.value
        if other.writable is not None:
            self.writable = other.writable
        if other.getter is not None:
            self.getter = other.getter
        if other.setter is not None:
            self.setter = other.setter
        if other.writable is not None:
            self.writable = other.writable
        if other.configurable is not None:
            self.configurable = other.configurable

class DataProperty(Property):
    def __init__(self, value = None, writable = None, enumerable = None, configurable = None):
        Property.__init__(self, value = value, writable = writable, enumerable = enumerable, configurable = configurable)

    def is_data_property(self):
        return True

class AccessorProperty(Property):
    def __init__(self, getter = None, setter = None, enumerable = None, configurable = None):
        Property.__init__(self, getter = getter, setter = setter, enumerable = enumerable, configurable = configurable)

    def is_accessor_property(self):
        return True

def is_data_descriptor(desc):
    if desc is w_Undefined:
        return False
    return desc.is_data_descriptor()

def is_accessor_descriptor(desc):
    if desc is w_Undefined:
        return False
    return desc.is_accessor_descriptor()

def is_generic_descriptor(desc):
    if desc is w_Undefined:
        return False
    return desc.is_generic_descriptor()

# 8.10
class PropertyDescriptor(object):
    value = None
    writable = None
    getter = None
    setter = None
    configurable = None
    enumerable = None

    def __init__(self, value = None, writable = None, getter = None, setter = None, configurable = None, enumerable = None):
        self.value = value
        self.writable = writable
        self.getter = getter
        self.setter = setter
        self.configurable = configurable
        self.enumerable = enumerable

    def is_accessor_descriptor(self):
        return self.getter is not None and self.setter is not None

    def is_data_descriptor(self):
        return self.value is not None and self.writable is not None

    def is_generic_descriptor(self):
        return self.is_accessor_descriptor() is False and self.is_data_descriptor() is False

    def is_empty(self):
        return self.getter is None\
            and self.setter is None\
            and self.value is None\
            and self.writable is None\
            and self.enumerable is None\
            and self.configurable is None

    def __eq__(self, other):
        assert isinstance(other, PropertyDescriptor)

        if self.setter is not None and self.setter != other.setter:
            return False

        if self.getter is not None and self.getter != other.getter:
            return False

        if self.writable is not None and self.writable != other.writable:
            return False

        if self.value is not None and self.value != other.value:
            return False

        if self.configurable is not None and self.configurable != other.configurable:
            return False

        if self.enumerable is not None and self.enumerable != other.enumerable:
            return False

    def update_with(self, other):
        assert isinstance(other, PropertyDescriptor)

        if other.enumerable is not None:
            self.enumerable = other.enumerable

        if other.configurable is not None:
            self.configurable = other.configurable

        if other.value is not None:
            self.value = other.value

        if other.writable is not None:
            self.writable = other.writable

        if other.getter is not None:
            self.getter = other.getter

        if other.setter is not None:
            self.setter = other.setter

class PropertyIdenfidier(object):
    def __init__(self, name, descriptor):
        self.name = name
        self.descriptor = descriptor

class W_ProtoGetter(W_Root):
    def is_callable(self):
        return True

    def Call(self, args = [], this = None, calling_context = None):
        if not isinstance(this, W_BasicObject):
            raise JsTypeError()

        return this._prototype_

class W_ProtoSetter(W_Root):
    def is_callable(self):
        return True

    def Call(self, args = [], this = None, calling_context = None):
        if not isinstance(this, W_BasicObject):
            raise JsTypeError()

        proto = args[0]
        this._prototype_ = proto

w_proto_getter = W_ProtoGetter()
w_proto_setter = W_ProtoSetter()
proto_desc = PropertyDescriptor(getter = w_proto_getter, setter = w_proto_setter, enumerable = False, configurable = False)

class W_BasicObject(W_Root):
    _type_ = 'object'
    _class_ = 'Object'
    _prototype_ = w_Null
    _extensible_ = True

    def __init__(self):
        W_Root.__init__(self)
        self._properties_ = {}

        #desc = PropertyDescriptor(value = self._prototype_, writable = False, enumerable = False, configurable = False)
        desc = proto_desc
        W_BasicObject.define_own_property(self, '__proto__', desc)

    def __repr__(self):
        return "%s: %s" % (object.__repr__(self), self.klass())


    ##########
    # 8.6.2 Object Internal Properties and Methods
    def prototype(self):
        return self._prototype_

    def klass(self):
        return self._class_

    def extensible(self):
        return self._extensible_

    # 8.12.3
    def get(self, p):
        desc = self.get_property(p)

        if desc is w_Undefined:
            return w_Undefined

        if is_data_descriptor(desc):
            return desc.value

        getter = desc.getter
        if getter is w_Undefined:
            return w_Undefined

        res = getter.Call(this = self)
        return res

    # 8.12.1
    def get_own_property(self, p):
        if p not in self._properties_:
            return w_Undefined

        d = PropertyDescriptor()
        x = self._properties_[p]

        if x.is_data_property():
            d.value = x.value
            d.writable = x.writable
        elif x.is_accessor_property:
            d.setter = x.setter
            d.getter = x.getter

        d.enumerable = x.enumerable
        d.configurable = x.configurable
        return d

    # 8.12.2
    def get_property(self, p):
        prop = self.get_own_property(p)
        if prop is not w_Undefined:
            return prop
        proto = self.prototype()

        if proto is w_Null:
            return w_Undefined

        return proto.get_property(p)

    # 8.12.5
    def put(self, p, v, throw = False):
        if self.can_put(p) is False:
            if throw is True:
                raise JsTypeError()
            else:
                return

        own_desc = self.get_own_property(p)
        if is_data_descriptor(own_desc) is True:
            value_desc = PropertyDescriptor(value = v)
            self.define_own_property(p, value_desc, throw)
            return

        desc = self.get_property(p)
        if is_accessor_descriptor(desc) is True:
            setter = desc.setter
            assert setter is not None
            setter.Call(this = self, args = [v])
        else:
            new_desc = PropertyDescriptor(value = v, writable = True, configurable = True, enumerable = True)
            self.define_own_property(p, new_desc, throw)

    # 8.12.4
    def can_put(self, p):
        desc = self.get_own_property(p)
        if desc is not w_Undefined:
            if is_accessor_descriptor(desc) is True:
                if desc.setter is w_Undefined:
                    return False
                else:
                    return True
            return desc.writable

        proto = self.prototype()

        if proto is w_Null or proto is w_Undefined:
            return self.extensible()

        inherited = proto.get_property(p)
        if inherited is w_Undefined:
            return self.extensible()

        if is_accessor_descriptor(inherited) is True:
            if inherited.setter is w_Undefined:
                return False
            else:
                return True
        else:
            if self.extensible() is False:
                return False
            else:
                return inherited.writable

    # 8.12.6
    def has_property(self, p):
        desc = self.get_property(p)
        if desc is w_Undefined:
            return False
        return True

    # 8.12.7
    def delete(self, p, throw = False):
        desc = self.get_own_property(p)
        if desc is w_Undefined:
            return True
        if desc.configurable:
            del self._properties_[p]
            return True

        if throw is True:
            raise JsTypeError()

        return False

    # 8.12.8
    def default_value(self, hint = 'Number'):
        if hint == 'String':
            res = self._default_value_string_()
            if res is None:
                res = self._default_value_number_()
        else:
            res = self._default_value_number_()
            if res is None:
                res = self._default_value_string_()

        if res is not None:
            return res

        raise JsTypeError()

    def _default_value_string_(self):
        to_string = self.get('toString')
        if to_string.is_callable():
            _str = to_string.Call(this = self)
            if isinstance(_str, W_Primitive):
                return _str

    def _default_value_number_(self):
        value_of = self.get('valueOf')
        if value_of.is_callable():
            val = value_of.Call(this = self)
            if isinstance(val, W_Primitive):
                return val

    # 8.12.9
    def define_own_property(self, p, desc, throw = False):
        def reject():
            if throw:
                raise JsTypeError()
            else:
                return False

        current = self.get_own_property(p)
        extensible = self.extensible()
        # 3.
        if current is w_Undefined and extensible is False:
            return reject()
        # 4.
        if current is w_Undefined and extensible is True:
            # 4.a
            if is_generic_descriptor(desc) or is_data_descriptor(desc):
                new_prop = DataProperty(\
                    value = desc.value,\
                    writable = desc.writable,\
                    enumerable = desc.enumerable,\
                    configurable = desc.configurable\
                )
                self._properties_[p] = new_prop
            # 4.b
            else:
                assert is_accessor_descriptor(desc) is True
                new_prop = AccessorProperty(\
                    getter = desc.getter,\
                    setter = desc.setter,\
                    enumerable = desc.enumerable,
                    configurable = desc.configurable\
                )
                self._properties_[p] = new_prop
            # 4.c
            return True

        # 5.
        if desc.is_empty():
            return True

        # 6.
        if desc == current:
            return True

        # 7.
        if current.configurable is False:
            if desc.configurable is True:
                return reject()
            if desc.enumerable is not None and current.enumerable != desc.enumerable:
                return reject()

        # 8.
        if is_generic_descriptor(desc):
            pass
        # 9.
        elif is_data_descriptor(current) != is_data_descriptor(desc):
            # 9.a
            if current.configurable is False:
                return reject()
            # 9.b
            if is_data_descriptor(current):
                raise NotImplementedError(self.__class__)
            # 9.c
            else:
                raise NotImplementedError(self.__class__)
        # 10
        elif is_data_descriptor(current) and is_data_descriptor(desc):
            # 10.a
            if current.configurable is False:
                # 10.a.i
                if current.writable is False and desc.writable is True:
                    return reject()
                # 10.a.ii
                if current.writable is False:
                    if desc.value is not None and desc.value != current.value:
                        return reject()
            # 10.b
            else:
                pass
        # 11
        elif is_accessor_descriptor(current) and is_accessor_descriptor(desc):
            # 11.a
            if current.configurable is False:
                # 11.a.i
                if desc.setter is not None and desc.setter != current.setter:
                    return reject()
                # 11.a.ii
                if desc.getter is not None and desc.getter != current.getter:
                    return reject()
        # 12
        prop = self._properties_[p]
        prop.update_with(desc)

        # 13
        return True

    ##########
    def ToBoolean(self):
        return True

    def ToNumber(self):
        return self.ToPrimitive('Number').ToNumber()

    def to_string(self):
        return self.ToPrimitive('String').to_string()

    def ToPrimitive(self, hint = None):
        return self.default_value(hint)

    def ToObject(self):
        return self

class W__PrimitiveObject(W_BasicObject):
    def __init__(self, primitive_value):
        W_BasicObject.__init__(self)
        self._primitive_value_ = _w(primitive_value)

    def PrimitiveValue(self):
        return self._primitive_value_

class W_BooleanObject(W__PrimitiveObject):
    _class_ = 'Boolean'

class W_NumericObject(W__PrimitiveObject):
    _class_ = 'Number'

class W_StringObject(W__PrimitiveObject):
    _class_ = 'String'
    def __init__(self, primitive_value):
        W__PrimitiveObject.__init__(self, primitive_value)
        length = len(self._primitive_value_.to_string())
        descr = PropertyDescriptor(value = _w(length), enumerable = False, configurable = False, writable = False)
        self.define_own_property('length', descr)

    def get_own_property(self, p):
        desc = super(W_StringObject, self).get_own_property(p)
        if desc is not w_Undefined:
            return desc

        if not is_array_index(p):
            return w_Undefined

        string = self.to_string()
        index = int(p)
        length = len(string)

        if len <= index:
            return w_Undefined

        result_string = string[index]
        d = PropertyDescriptor(value = _w(result_string), enumerable = True, writable = False, configurable = False)
        return d

class W_DateObject(W__PrimitiveObject):
    _class_ = 'Date'

class W__Object(W_BasicObject):
    pass

class W_GlobalObject(W__Object):
    _class_ = 'global'

class W_BasicFunction(W_BasicObject):
    _class_ = 'Function'
    _type_ = 'function'

    def Call(self, args = [], this = None, calling_context = None):
        raise NotImplementedError("abstract")

    # 13.2.2
    def Construct(self, args=[]):
        obj = W__Object()
        proto = self.get('prototype')
        if isinstance(proto, W_BasicObject):
            obj._prototype_ = proto
        else:
            # would love to test this
            # but I fail to find a case that falls into this
            obj._prototype_ = W__Object._prototype_

        result = self.Call(args, this=obj)
        if isinstance(result, W__Object):
            return result

        return obj

    def is_callable(self):
        return True

    def _to_string_(self):
        return 'function() {}'

class W_ObjectConstructor(W_BasicFunction):
    def Call(self, args = [], this = None, calling_context = None):
        from js.builtins import get_arg
        value = get_arg(args, 0)

        if isinstance(value, W_BasicObject):
            return value
        if isinstance(value, W_String):
            return value.ToObject()
        if isinstance(value, W_Boolean):
            return value.ToObject()
        if isinstance(value, W_Number):
            return value.ToObject()

        assert isnull_or_undefined(value)

        obj = W__Object()
        return obj

    # TODO
    def Construct(self, args=[]):
        return self.Call(args, this=None)

class W_FunctionConstructor(W_BasicFunction):
    def _to_string_(self):
        return "function Function() { [native code] }"

    # 15.3.2.1
    def Call(self, args = [], this = None, calling_context = None):
        arg_count = len(args)
        p = ''
        if arg_count == 0:
            body = ''
        elif arg_count == 1:
            body = args[0].to_string()
        else:
            first_arg = args[0]
            p = first_arg.to_string()
            k = 2
            while k < arg_count:
                next_arg = args[k-1]
                p = "%s, %s" % (p, next_arg.to_string())
                k = k + 1
            body = args[k-1].to_string()

        src = "function (%s) { %s }" % (p, body)

        from js.astbuilder import parse_to_ast
        from js.jscode import ast_to_bytecode

        ast = parse_to_ast(src)
        symbol_map = ast.symbol_map
        code = ast_to_bytecode(ast, symbol_map)
        # TODO hackish
        func = code.opcodes[0].funcobj

        from js.execution_context import get_global_environment
        scope = get_global_environment()
        strict = func.strict
        params = func.params()
        w_func = W__Function(func, formal_parameter_list = params, scope = scope, strict = strict)
        return w_func

    # TODO
    def Construct(self, args=[]):
        return self.Call(args, this=None)

# 15.7.2
class W_NumberConstructor(W_BasicFunction):
    # 15.7.1.1
    def Call(self, args = [], this = None, calling_context = None):
        if len(args) >= 1 and not isnull_or_undefined(args[0]):
            return _w(args[0].ToNumber())
        elif len(args) >= 1 and args[0] is w_Undefined:
            return _w(NAN)
        else:
            return _w(0.0)

    # 15.7.2.1
    def Construct(self, args=[]):
        return self.Call(args).ToObject()

    def _to_string_(self):
        return "function Number() { [native code] }"

# 15.5.2
class W_StringConstructor(W_BasicFunction):
    def Call(self, args = [], this = None, calling_context = None):
        if len(args) >= 1:
            return W_String(args[0].to_string())
        else:
            return W_String('')

    def Construct(self, args=[]):
        return self.Call(args).ToObject()

    def _to_string_(self):
        return "function String() { [native code] }"

# 15.6.2
class W_BooleanConstructor(W_BasicFunction):
    def Call(self, args = [], this = None, calling_context = None):
        if len(args) >= 1 and not isnull_or_undefined(args[0]):
            return _w(args[0].ToBoolean())
        else:
            return _w(False)

    def Construct(self, args=[]):
        return self.Call(args).ToObject()

    def _to_string_(self):
        return "function Boolean() { [native code] }"

# 15.9.2
class W_DateConstructor(W_BasicFunction):
    def Call(self, args=[], this=None):
        import time
        return W_DateObject(_w(int(time.time()*1000)))

    # 15.7.2.1
    def Construct(self, args=[]):
        return self.Call(args).ToObject()

    def _to_string_(self):
        return "function Date() { [native code] }"


class W__Function(W_BasicFunction):

    def __init__(self, function_body, formal_parameter_list=[], scope=None, strict=False):
        W_BasicFunction.__init__(self)
        self._function_ = function_body
        self._scope_ = scope
        self._params_ = formal_parameter_list
        self._strict_ = strict

        # 13.2 Creating Function Objects
        # 14.
        _len = len(formal_parameter_list)
        # 15.
        put_property(self, 'length', _w(_len), writable = False, enumerable = False, configurable = False)
        # 16.
        proto_obj = W__Object()
        # 17.
        put_property(proto_obj, 'constructor', self, writable = True, enumerable = False, configurable = True)
        # 18.
        put_property(self, 'prototype', proto_obj, writable = True, enumerable = False, configurable = False)

        if strict is True:
            raise NotImplementedError()
        else:
            put_property(self, 'caller', w_Null, writable = True, enumerable = False, configurable = False)
            put_property(self, 'arguments', w_Null, writable = True, enumerable = False, configurable = False)


    def _to_string(self):
        return self._function_.to_string()

    def code(self):
        return self._function_

    def formal_parameters(self):
        return self._params_

    def Call(self, args = [], this = None, calling_context = None):
        from js.execution_context import FunctionExecutionContext
        code = self.code()
        argn = self.formal_parameters()
        strict = self._strict_
        scope = self.scope()

        ctx = FunctionExecutionContext(code,\
            formal_parameters = argn,\
            argv = args,\
            this = this,\
            strict = strict,\
            scope = scope,\
            w_func = self)
        ctx._calling_context_ = calling_context

        res = code.run(ctx)
        return res

    # 15.3.5.4
    def get(self, p):
        v = W_BasicObject.get(self, p)
        if p is 'caller' and isinstance(v, W__Function) and v.is_strict():
            raise JsTypeError()
        return v

    def scope(self):
        return self._scope_

    def is_strict(self):
        return self._strict_

# 10.6
class W_Arguments(W__Object):
    _class_ = 'Arguments'

    def __init__(self, func, names, args, env, strict = False):
        W__Object.__init__(self)
        self.strict = strict
        _len = len(args)
        put_property(self, 'length', _w(_len), writable = True, enumerable = False, configurable = True)

        _map = W__Object()
        mapped_names = []
        indx = _len - 1
        while indx >= 0:
            val = args[indx]
            put_property(self, str(indx), val, writable = True, enumerable = True, configurable = True)
            if indx < len(names):
                name = names[indx]
                if strict is False and name not in mapped_names:
                    mapped_names.append(name)
                    g = make_arg_getter(name, env)
                    p = make_arg_setter(name, env)
                    desc = PropertyDescriptor(setter = p, getter = g, configurable = True)
                    _map.define_own_property(str(indx), desc, False)
            indx = indx - 1

        if len(mapped_names) > 0:
            self._paramenter_map_ = _map

        if strict is False:
            put_property(self, 'callee', _w(func), writable = True, enumerable = False, configurable = True)
        else:
            # 10.6 14 thrower
            pass

    #def get(self, p):
        #if self.strict:
            #return super(W_Arguments, self).get(p)

        #_map = self._paramenter_map_
        #is_mapped = _map.get_own_property(p)
        #if is_mapped is w_Undefined:
            #v = super(W_Arguments, self).get(p)
            #return v
        #else:
            #return _map.get(p)

    #def get_own_property(self, p):
        #if self.strict:
            #return super(W_Arguments, self).get_own_property(p)

        #desc = super(W_Arguments, self).get_own_property(p)
        #if desc is w_Undefined:
            #return desc

        #_map = self._paramenter_map_
        #is_mapped = _map.get_own_property(p)
        #if not is_mapped is w_Undefined:
            #value = _map.get(p)
            #desc.value = value

        #return desc

    #def define_own_property(self, p, desc, throw = False):
        #if self.strict:
            #return super(W_Arguments, self).define_own_property(p, desc, throw)

        #_map = self._paramenter_map_
        #is_mapped = _map.get_own_property(p)
        #allowed = super(W_Arguments, self).define_own_property(p, desc, False)

        #if allowed is False:
            #if throw:
                #raise JsTypeError()
            #else:
                #return False

        #if is_mapped is not w_Undefined:
            #if is_accessor_descriptor(desc):
                #_map.delete(p, False)
            #else:
                #if desc.value is not None:
                    #_map.put(p, desc.value, throw)
                #if desc.writable is False:
                    #_map.delete(p, False)

        #return True

    #def delete(self, p, throw = False):
        #if self.strict:
            #return super(W_Arguments, self).delete(p, throw)

        #_map = self._paramenter_map_
        #is_mapped = _map.get_own_property(p)
        #result = super(W_Arguments, self).delete(p, throw)
        #if result is True and is_mapped is not w_Undefined:
            #_map.delete(p, False)

        #return result

def make_arg_getter(name, env):
    code = 'return %s;' % (name)

def make_arg_setter(name, env):
    param = '%s_arg' % (name)
    code = '%s = %s;' % (name, param)

# 15.4.2
class W_ArrayConstructor(W_BasicFunction):
    def __init__(self):
        W_BasicFunction.__init__(self)
        put_property(self, 'length', _w(1), writable = False, enumerable = False, configurable = False)

    def is_callable(self):
        return True

    def Call(self, args = [], this = None, calling_context = None):
        if len(args) == 1:
            _len = args[0]
            if isinstance(_len, W_Number):
                length = _len.ToUInt32()
                if length != _len.ToNumber():
                    raise JsRangeError()
                array = W__Array(length)
            else:
                length = 1
                array = W__Array(length)
                array.put('0', _len)

            return array
        else:
            array = W__Array()
            for index, obj in enumerate(args):
                array.put(str(index), obj)
            return array

    def Construct(self, args=[]):
        return self.Call(args)

class W__Array(W_BasicObject):
    _class_ = 'Array'

    def __init__(self, length = 0):
        W_BasicObject.__init__(self)

        desc = PropertyDescriptor(value = _w(length), writable = True, enumerable = False, configurable = False)
        W_BasicObject.define_own_property(self, 'length', desc)

    # 15.4.5.1
    def define_own_property(self, p, desc, throw = False):
        def reject():
            if throw:
                raise JsTypeError()
            else:
                return False

        old_len_desc = self.get_own_property('length')
        assert old_len_desc is not w_Undefined
        old_len = old_len_desc.value.ToUInt32()

        # 3
        if p == 'length':
            if desc.value is None:
                return W_BasicObject.define_own_property(self, 'length', desc, throw)
            import copy
            new_len_desc = copy.deepcopy(desc)
            new_len = desc.value.ToUInt32()

            if new_len != desc.value.ToNumber():
                raise JsRangeError()

            new_len_desc.value = _w(new_len)

            # f
            if new_len >= old_len:
                return W_BasicObject.define_own_property(self, 'length', new_len_desc, throw)
            # g
            if old_len_desc.writable is False:
                return reject()

            # h
            if new_len_desc.writable is None or new_len_desc.writable is true:
                new_writable = True
            # i
            else:
                new_len_desc.writable = True
                new_writable = False

            # j
            succeeded = W_BasicObject.define_own_property(self, 'length', new_len_desc, throw)
            # k
            if succeeded is False:
                return False

            # l
            while new_len < old_len:
                old_len = old_len - 1
                delete_succeeded = self.delete(str(old_len), False)
                if delete_succeeded is False:
                    new_len_desc.value = _w(old_len + 1)
                    if new_writable is False:
                        new_len_desc.writable = False
                    W_BasicObject.define_own_property(self, 'length', new_len_desc, False)
                    return reject()

            # m
            if new_writable is False:
                desc = PropertyDescriptor(writable = False)
                res = W_BasicObject.define_own_property(self, 'length', desc, False)
                assert res is True

            return True

        # 4
        elif is_array_index(p):
            # a
            index = r_uint32(int(p))
            # b
            if index >= old_len and old_len_desc.writable is False:
                return reject()

            # c
            succeeded = W_BasicObject.define_own_property(self, p, desc, False)
            # d
            if succeeded is False:
                return reject()

            # e
            if index >= old_len:
                old_len_desc.value = _w(index + 1)
                res = W_BasicObject.define_own_property(self, 'length', old_len_desc, False)
                assert res is True
            # f
            return True
        # 5
        return W_BasicObject.define_own_property(self, p, desc, throw)

def is_array_index(p):
    try:
        return str(r_uint32(abs(int(p)))) == p
    except ValueError:
        return False

# 15.8
class W_Math(W__Object):
    _class_ = 'Math'

class W_Boolean(W_Primitive):
    _type_ = 'boolean'

    def __init__(self, boolval):
        W_Primitive.__init__(self)
        self._boolval_ = bool(boolval)

    def __repr__(self):
        return 'W_Bool(%s)' % (str(self._boolval_), )

    def ToObject(self):
        return W_BooleanObject(self)

    def to_string(self):
        if self._boolval_ == True:
            return "true"
        return "false"

    def ToNumber(self):
        if self._boolval_ == True:
            return 1.0
        return 0.0

    def ToBoolean(self):
        return self._boolval_

class W_String(W_Primitive):
    _type_ = 'string'

    def __init__(self, strval):
        assert isinstance(strval, str) or isinstance(strval, unicode)
        W_Primitive.__init__(self)
        self._strval_ = strval

    def __eq__(self, other):
        other_string = other.to_string()
        return self.to_string() == other_string

    def __repr__(self):
        return 'W_String(%s)' % (repr(self._strval_),)

    def ToObject(self):
        return W_StringObject(self)

    def to_string(self):
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
                except OverflowError:
                    return INFINITY
            except OverflowError:
                return INFINITY
        except OverflowError:
            return INFINITY

class W_Number(W_Primitive):
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

    def __eq__(self, other):
        if isinstance(other, W_Number):
            return self.ToNumber() == other.ToNumber()
        else:
            return False

class W_IntNumber(W_Number):
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

    def to_string(self):
        # XXX incomplete, this doesn't follow the 9.8.1 recommendation
        return str(self.ToInteger())

def r_int32(n):
    return intmask(rffi.cast(rffi.INT, n))

def r_uint32(n):
    return intmask(rffi.cast(rffi.UINT, n))

class W_FloatNumber(W_Number):
    """ Number known to be a float
    """
    def __init__(self, floatval):
        assert isinstance(floatval, float)
        W_Number.__init__(self)
        self._floatval_ = float(floatval)

    def __repr__(self):
        return 'W_FloatNumber(%s)' % (self._floatval_,)

    def to_string(self):
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


def isnull_or_undefined(obj):
    if obj is w_Null or obj is w_Undefined:
        return True
    return False

w_True = W_Boolean(True)
w_False = W_Boolean(False)

def newbool(val):
    if val:
        return w_True
    return w_False

class W_List(W_Root):
    def __init__(self, values):
        self.values = values

    def to_list(self):
        return self.values

class W_Iterator(W_Root):
    def __init__(self, elements_w):
        self.elements_w = elements_w

    def next(self):
        if self.elements_w:
            return self.elements_w.pop()

    def empty(self):
        return len(self.elements_w) == 0

def _w(value):
    if isinstance(value, W_Root):
        return value
    elif isinstance(value, bool):
        return newbool(value)
    elif isinstance(value, (int, long)):
        return W_IntNumber(value)
    elif isinstance(value, float):
        return W_FloatNumber(value)
    elif isinstance(value, basestring):
        return W_String(value)
    elif isinstance(value, list):
        a = W__Array()
        for index, item in enumerate(value):
            put_property(a, str(index), _w(item), writable = True, enumerable = True, configurable = True)
        return a

    elif value is None:
        return w_Null
    raise TypeError(value)

def put_property(obj, name, value, writable = False, configurable = False, enumerable = False, throw = False):
    descriptor = PropertyDescriptor(value = value, writable = writable, configurable = configurable, enumerable = enumerable)
    obj.define_own_property(name, descriptor, throw)
