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
        return u''

    def type(self):
        return self._type_

    def to_boolean(self):
        return False

    def ToPrimitive(self, hint = None):
        return self

    def ToObject(self):
        raise JsTypeError(u'W_Root.ToObject')

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
        return unicode(self._type_)

    def check_object_coercible(self):
        raise JsTypeError(u'W_Undefined.check_object_coercible')

class W_Null(W_Primitive):
    _type_ = 'null'

    def to_boolean(self):
        return False

    def to_string(self):
        return u'null'

    def check_object_coercible(self):
        raise JsTypeError(u'W_Null.check_object_coercible')

w_Undefined = W_Undefined()
w_Null = W_Null()

NOT_SET = -1

# 8.6.1
class Property(object):
    def __init__(self, value = None, writable = NOT_SET, getter = None, setter = None, enumerable = NOT_SET, configurable = NOT_SET):
        self.value = value
        self.writable = writable
        self.getter = getter
        self.setter = setter
        self.enumerable = enumerable
        self.configurable = configurable

    def is_data_property(self):
        return False

    def is_accessor_property(self):
        return False

    def update_with(self, other):
        if other.value is not None:
            self.value = other.value
        if other.writable is not NOT_SET:
            self.writable = other.writable
        if other.getter is not None:
            self.getter = other.getter
        if other.setter is not None:
            self.setter = other.setter
        if other.writable is not NOT_SET:
            self.writable = other.writable
        if other.configurable is not NOT_SET:
            self.configurable = other.configurable

class DataProperty(Property):
    def __init__(self, value = None, writable = NOT_SET, enumerable = NOT_SET, configurable = NOT_SET):
        Property.__init__(self, value = value, writable = writable, enumerable = enumerable, configurable = configurable)

    def is_data_property(self):
        return True

class AccessorProperty(Property):
    def __init__(self, getter = None, setter = None, enumerable = NOT_SET, configurable = NOT_SET):
        Property.__init__(self, getter = getter, setter = setter, enumerable = enumerable, configurable = configurable)

    def is_accessor_property(self):
        return True

def is_data_descriptor(desc):
    if desc is None:
        return False
    return desc.is_data_descriptor()

def is_accessor_descriptor(desc):
    if desc is None:
        return False
    return desc.is_accessor_descriptor()

def is_generic_descriptor(desc):
    if desc is None:
        return False
    return desc.is_generic_descriptor()

# 8.10
class PropertyDescriptor(object):

    def __init__(self, value = None, writable = NOT_SET, getter = None, setter = None, configurable = NOT_SET, enumerable = NOT_SET):
        self.value = value
        self.writable = writable
        self.getter = getter
        self.setter = setter
        self.configurable = configurable
        self.enumerable = enumerable

    def is_accessor_descriptor(self):
        return self.getter is not None and self.setter is not None

    def is_data_descriptor(self):
        return self.value is not None and self.writable is not NOT_SET

    def is_generic_descriptor(self):
        return self.is_accessor_descriptor() is False and self.is_data_descriptor() is False

    def is_empty(self):
        return self.getter is None\
            and self.setter is None\
            and self.value is None\
            and self.writable is NOT_SET\
            and self.enumerable is NOT_SET\
            and self.configurable is NOT_SET

    def __eq__(self, other):
        assert isinstance(other, PropertyDescriptor)

        if self.setter is not None and self.setter != other.setter:
            return False

        if self.getter is not None and self.getter != other.getter:
            return False

        if self.writable is not NOT_SET and self.writable != other.writable:
            return False

        if self.value is not None and self.value != other.value:
            return False

        if self.configurable is not NOT_SET and self.configurable != other.configurable:
            return False

        if self.enumerable is not NOT_SET and self.enumerable != other.enumerable:
            return False

    def update_with(self, other):
        assert isinstance(other, PropertyDescriptor)

        if other.enumerable is not NOT_SET:
            self.enumerable = other.enumerable

        if other.configurable is not NOT_SET:
            self.configurable = other.configurable

        if other.value is not None:
            self.value = other.value

        if other.writable is not NOT_SET:
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
            raise JsTypeError(u'')

        return this._prototype_

class W_ProtoSetter(W_Root):
    def is_callable(self):
        return True

    def Call(self, args = [], this = None, calling_context = None):
        if not isinstance(this, W_BasicObject):
            raise JsTypeError(u'')

        proto = args[0]
        this._prototype_ = proto

w_proto_getter = W_ProtoGetter()
w_proto_setter = W_ProtoSetter()
proto_desc = PropertyDescriptor(getter = w_proto_getter, setter = w_proto_setter, enumerable = False, configurable = False)

def reject(throw):
    if throw:
        raise JsTypeError(u'')
    return False

class W_BasicObject(W_Root):
    _type_ = 'object'
    _class_ = 'Object'
    _extensible_ = True

    def __init__(self):
        W_Root.__init__(self)
        self._properties_ = {}
        self._prototype_ = w_Null
        desc = proto_desc
        W_BasicObject.define_own_property(self, u'__proto__', desc)

    def __str__(self):
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
        assert isinstance(p, unicode)
        desc = self.get_property(p)

        if desc is None:
            return w_Undefined

        if is_data_descriptor(desc):
            return desc.value

        getter = desc.getter
        if getter is None:
            return w_Undefined

        res = getter.Call(this = self)
        return res

    # 8.12.1
    def get_own_property(self, p):
        assert isinstance(p, unicode)
        if p not in self._properties_:
            return None

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
        assert isinstance(p, unicode)

        prop = self.get_own_property(p)
        if prop is not None:
            return prop

        proto = self.prototype()
        if proto is w_Null:
            return None

        return proto.get_property(p)

    # 8.12.5
    def put(self, p, v, throw = False):
        assert isinstance(p, unicode)
        if self.can_put(p) is False:
            if throw is True:
                raise JsTypeError(u'')
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
        if desc is not None:
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
        if inherited is None:
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
        assert isinstance(p, unicode)
        desc = self.get_property(p)
        if desc is None:
            return False
        return True

    # 8.12.7
    def delete(self, p, throw = False):
        desc = self.get_own_property(p)
        if desc is None:
            return True
        if desc.configurable:
            del self._properties_[p]
            return True

        if throw is True:
            raise JsTypeError(u'')

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

        raise JsTypeError(u'')

    def _default_value_string_(self):
        to_string = self.get(u'toString')
        if to_string.is_callable():
            _str = to_string.Call(this = self)
            if isinstance(_str, W_Primitive):
                return _str

    def _default_value_number_(self):
        value_of = self.get(u'valueOf')
        if value_of.is_callable():
            val = value_of.Call(this = self)
            if isinstance(val, W_Primitive):
                return val

    # 8.12.9
    def define_own_property(self, p, desc, throw = False):
        current = self.get_own_property(p)
        extensible = self.extensible()
        # 3.
        if current is None and extensible is False:
            return reject(throw)
        # 4.
        if current is None and extensible is True:
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
                return reject(throw)
            if desc.enumerable is not NOT_SET and current.enumerable != desc.enumerable:
                return reject(throw)

        # 8.
        if is_generic_descriptor(desc):
            pass
        # 9.
        elif is_data_descriptor(current) != is_data_descriptor(desc):
            # 9.a
            if current.configurable is False:
                return reject(throw)
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
                    return reject(throw)
                # 10.a.ii
                if current.writable is False:
                    if desc.value is not None and desc.value != current.value:
                        return reject(throw)
            # 10.b
            else:
                pass
        # 11
        elif is_accessor_descriptor(current) and is_accessor_descriptor(desc):
            # 11.a
            if current.configurable is False:
                # 11.a.i
                if desc.setter is not None and desc.setter != current.setter:
                    return reject(throw)
                # 11.a.ii
                if desc.getter is not None and desc.getter != current.getter:
                    return reject(throw)
        # 12
        prop = self._properties_[p]
        prop.update_with(desc)

        # 13
        return True

    ##########
    def to_boolean(self):
        return True

    def ToNumber(self):
        return self.ToPrimitive('Number').ToNumber()

    def to_string(self):
        return self.ToPrimitive('String').to_string()

    def ToPrimitive(self, hint = None):
        return self.default_value(hint)

    def ToObject(self):
        return self

    def has_instance(self, other):
        raise JsTypeError(u'has_instance')
    ###

    def _named_properties_dict(self):
        my_d = {}
        for i in self._properties_.keys():
            my_d[i] = None

        proto = self.prototype()
        if not isnull_or_undefined(proto):
            proto_d = proto._named_properties_dict()
        else:
            proto_d = {}

        my_d.update(proto_d)

        return my_d

    def named_properties(self):
        prop_dict = self._named_properties_dict()
        return prop_dict.keys()

class W__PrimitiveObject(W_BasicObject):
    def __init__(self, primitive_value):
        W_BasicObject.__init__(self)
        self.set_primitive_value(primitive_value)

    def PrimitiveValue(self):
        return self._primitive_value_

    def set_primitive_value(self, value):
        assert isinstance(value, W_Root)
        self._primitive_value_ = value

class W_BooleanObject(W__PrimitiveObject):
    _class_ = 'Boolean'

    def __str__(self):
        return u'W_BooleanObject(%s)' % (str(self._primitive_value_))

class W_NumericObject(W__PrimitiveObject):
    _class_ = 'Number'

class W_StringObject(W__PrimitiveObject):
    _class_ = 'String'
    def __init__(self, primitive_value):
        W__PrimitiveObject.__init__(self, primitive_value)
        length = len(self._primitive_value_.to_string())
        descr = PropertyDescriptor(value = _w(length), enumerable = False, configurable = False, writable = False)
        self.define_own_property(u'length', descr)

    def get_own_property(self, p):
        desc = W__PrimitiveObject.get_own_property(self, p)
        if desc is not None:
            return desc

        if not is_array_index(p):
            return None

        string = self.to_string()
        index = int(p)
        length = len(string)

        if length <= index:
            return None

        result_string = string[index]
        d = PropertyDescriptor(value = _w(result_string), enumerable = True, writable = False, configurable = False)
        return d

class W__Object(W_BasicObject):
    pass

class W_GlobalObject(W__Object):
    _class_ = 'global'

class W_DateObject(W__PrimitiveObject):
    _class_ = 'Date'
    def default_value(self, hint = 'String'):
        if hint is None:
            hint = 'String'
        return W_BasicObject.default_value(self, hint)

class W_BasicFunction(W_BasicObject):
    _class_ = 'Function'
    _type_ = 'function'

    def Call(self, args = [], this = None, calling_context = None):
        raise NotImplementedError("abstract")

    # 13.2.2
    def Construct(self, args=[]):
        from js.object_space import object_space

        proto = self.get(u'prototype')
        if isinstance(proto, W_BasicObject):
            obj = object_space.new_obj_with_proto(W__Object, proto)
        else:
            # would love to test this
            # but I fail to find a case that falls into this
            obj = object_space.new_obj(W__Object)

        result = self.Call(args, this=obj)
        if isinstance(result, W__Object):
            return result

        return obj

    def is_callable(self):
        return True

    def _to_string_(self):
        return 'function() {}'

    # 15.3.5.3
    def has_instance(self, v):
        if not isinstance(v, W_BasicObject):
            return False

        o = self.get(u'prototype')

        if not isinstance(o, W_BasicObject):
            raise JsTypeError(u'has_instance')

        while True:
            v = v.prototype()
            if isnull_or_undefined(v):
                return False
            if v == o:
                return True

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

        from js.object_space import object_space
        obj = object_space.new_obj(W__Object)
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
        _args = u''
        body = u''
        if arg_count == 0:
            pass
        elif arg_count == 1:
            body = args[0].to_string()
        else:
            first_arg = args[0].to_string()
            _args = first_arg
            k = 2
            while k < arg_count:
                next_arg = args[k-1].to_string()
                _args = _args + u',' + next_arg
                k = k + 1
            body = args[k-1].to_string()

        src = u'function (' + _args + u') { ' + body + u' };'

        from js.astbuilder import parse_to_ast
        from js.jscode import ast_to_bytecode

        ast = parse_to_ast(src)
        symbol_map = ast.symbol_map
        code = ast_to_bytecode(ast, symbol_map)
        # TODO hackish
        func = code.opcodes[0].funcobj

        from js.object_space import object_space
        scope = object_space.get_global_environment()
        strict = func.strict
        params = func.params()
        w_func = object_space.new_obj(W__Function, func, formal_parameter_list = params, scope = scope, strict = strict)
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
        return u'function Number() { [native code] }'

# 15.5.2
class W_StringConstructor(W_BasicFunction):
    def Call(self, args = [], this = None, calling_context = None):
        from js.builtins import get_arg
        arg0 = get_arg(args, 0)
        strval = arg0.to_string()
        return W_String(strval)

    def Construct(self, args=[]):
        return self.Call(args).ToObject()

    def _to_string_(self):
        return u'function String() { [native code] }'

# 15.6.2
class W_BooleanConstructor(W_BasicFunction):
    def Call(self, args = [], this = None, calling_context = None):
        if len(args) >= 1 and not isnull_or_undefined(args[0]):
            boolval = args[0].to_boolean()
            return _w(boolval)
        else:
            return _w(False)

    def Construct(self, args=[]):
        return self.Call(args).ToObject()

    def _to_string_(self):
        return u'function Boolean() { [native code] }'

# 15.9.2
class W_DateConstructor(W_BasicFunction):
    def Call(self, args=[], this=None):
        from js.builtins import get_arg
        import time
        import datetime

        if len(args) > 1:
            arg0 = get_arg(args, 0);
            arg1 = get_arg(args, 1, _w(0));
            arg2 = get_arg(args, 2, _w(0));

            year = arg0.ToInteger()
            month = arg1.ToInteger() + 1
            day = arg2.ToInteger() + 1

            d = datetime.date(year, month, day)
            sec = time.mktime(d.timetuple())
            value = _w(int(sec * 1000))

        elif len(args) == 1:
            arg0 = get_arg(args, 0);
            if isinstance(arg0, W_String):
                raise NotImplementedError()
            else:
                num = arg0.ToNumber()
                if isnan(num) or isinf(num):
                    raise JsTypeError(unicode(num))
                value = _w(int(num))
        else:
            value = _w(int(time.time() * 1000))

        from js.object_space import object_space
        obj = object_space.new_obj(W_DateObject, value)
        return obj

    # 15.7.2.1
    def Construct(self, args=[]):
        return self.Call(args).ToObject()

    def _to_string_(self):
        return u'function Date() { [native code] }'


class W__Function(W_BasicFunction):

    def __init__(self, function_body, formal_parameter_list=[], scope=None, strict=False):
        from js.object_space import object_space
        W_BasicFunction.__init__(self)
        self._function_ = function_body
        self._scope_ = scope
        self._params_ = formal_parameter_list
        self._strict_ = strict

        # 13.2 Creating Function Objects
        # 14.
        _len = len(formal_parameter_list)
        # 15.
        put_property(self, u'length', _w(_len), writable = False, enumerable = False, configurable = False)
        # 16.
        proto_obj = object_space.new_obj(W__Object)
        # 17.
        put_property(proto_obj, u'constructor', self, writable = True, enumerable = False, configurable = True)
        # 18.
        put_property(self, u'prototype', proto_obj, writable = True, enumerable = False, configurable = False)

        if strict is True:
            raise NotImplementedError()
        else:
            put_property(self, u'caller', w_Null, writable = True, enumerable = False, configurable = False)
            put_property(self, u'arguments', w_Null, writable = True, enumerable = False, configurable = False)


    def _to_string(self):
        return self._function_.to_string()

    def code(self):
        return self._function_

    def formal_parameters(self):
        return self._params_

    def Call(self, args = [], this = None, calling_context = None):
        from js.execution_context import FunctionExecutionContext
        from js.completion import Completion

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

        assert isinstance(res, Completion)
        return res.value

    # 15.3.5.4
    def get(self, p):
        v = W_BasicObject.get(self, p)
        if p is u'caller' and isinstance(v, W__Function) and v.is_strict():
            raise JsTypeError(u'')
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
        put_property(self, u'length', _w(_len), writable = True, enumerable = False, configurable = True)

        from js.object_space import object_space
        _map = object_space.new_obj(W__Object)
        mapped_names = []
        indx = _len - 1
        while indx >= 0:
            val = args[indx]
            put_property(self, unicode(str(indx)), val, writable = True, enumerable = True, configurable = True)
            if indx < len(names):
                name = names[indx]
                if strict is False and name not in mapped_names:
                    mapped_names.append(name)
                    g = make_arg_getter(name, env)
                    p = make_arg_setter(name, env)
                    desc = PropertyDescriptor(setter = p, getter = g, configurable = True)
                    _map.define_own_property(unicode(str(indx)), desc, False)
            indx = indx - 1

        if len(mapped_names) > 0:
            self._paramenter_map_ = _map

        if strict is False:
            put_property(self, u'callee', _w(func), writable = True, enumerable = False, configurable = True)
        else:
            # 10.6 14 thrower
            pass

def make_arg_getter(name, env):
    code = u'return %s;' % (name)

def make_arg_setter(name, env):
    param = u'%s_arg' % (name)
    code = u'%s = %s;' % (name, param)

# 15.4.2
class W_ArrayConstructor(W_BasicFunction):
    def __init__(self):
        W_BasicFunction.__init__(self)
        put_property(self, u'length', _w(1), writable = False, enumerable = False, configurable = False)

    def is_callable(self):
        return True

    def Call(self, args = [], this = None, calling_context = None):
        from js.object_space import object_space

        if len(args) == 1:
            _len = args[0]
            if isinstance(_len, W_Number):
                length = _len.ToUInt32()
                if length != _len.ToNumber():
                    raise JsRangeError()
                array = object_space.new_obj(W__Array, length)
            else:
                length = 1
                array = object_space.new_obj(W__Array, length)
                array.put(u'0', _len)

            return array
        else:
            array = object_space.new_obj(W__Array)
            for index, obj in enumerate(args):
                array.put(unicode(str(index)), obj)
            return array

    def Construct(self, args=[]):
        return self.Call(args)

class W__Array(W_BasicObject):
    _class_ = 'Array'

    def __init__(self, length = 0):
        W_BasicObject.__init__(self)

        desc = PropertyDescriptor(value = _w(length), writable = True, enumerable = False, configurable = False)
        W_BasicObject.define_own_property(self, u'length', desc)

    # 15.4.5.1
    def define_own_property(self, p, desc, throw = False):
        old_len_desc = self.get_own_property(u'length')
        assert old_len_desc is not None
        old_len = old_len_desc.value.ToUInt32()

        # 3
        if p == u'length':
            if desc.value is None:
                return W_BasicObject.define_own_property(self, u'length', desc, throw)
            new_len_desc = PropertyDescriptor()
            new_len_desc.value = desc.value
            new_len_desc.writable = desc.writable
            new_len_desc.getter = desc.getter
            new_len_desc.setter = desc.setter
            new_len_desc.configurable = desc.configurable
            new_len_desc.enumerable = desc.enumerable
            new_len = desc.value.ToUInt32()

            if new_len != desc.value.ToNumber():
                raise JsRangeError()

            new_len_desc.value = _w(new_len)

            # f
            if new_len >= old_len:
                return W_BasicObject.define_own_property(self, u'length', new_len_desc, throw)
            # g
            if old_len_desc.writable is False:
                return reject(throw)

            # h
            if new_len_desc.writable is None or new_len_desc.writable is True:
                new_writable = True
            # i
            else:
                new_len_desc.writable = True
                new_writable = False

            # j
            succeeded = W_BasicObject.define_own_property(self, u'length', new_len_desc, throw)
            # k
            if succeeded is False:
                return False

            # l
            while new_len < old_len:
                old_len = old_len - 1
                delete_succeeded = self.delete(unicode(str(old_len)), False)
                if delete_succeeded is False:
                    new_len_desc.value = _w(old_len + 1)
                    if new_writable is False:
                        new_len_desc.writable = False
                    W_BasicObject.define_own_property(self, u'length', new_len_desc, False)
                    return reject(throw)

            # m
            if new_writable is False:
                desc = PropertyDescriptor(writable = False)
                res = W_BasicObject.define_own_property(self, u'length', desc, False)
                assert res is True

            return True

        # 4
        elif is_array_index(p):
            assert isinstance(p, unicode)
            # a
            index = r_uint32(int(p))
            # b
            if index >= old_len and old_len_desc.writable is False:
                return reject(throw)

            # c
            succeeded = W_BasicObject.define_own_property(self, p, desc, False)
            # d
            if succeeded is False:
                return reject(throw)

            # e
            if index >= old_len:
                old_len_desc.value = _w(index + 1)
                res = W_BasicObject.define_own_property(self, u'length', old_len_desc, False)
                assert res is True
            # f
            return True
        # 5
        return W_BasicObject.define_own_property(self, p, desc, throw)

def is_array_index(p):
    try:
        return unicode(str(r_uint32(abs(int(p))))) == p
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

    def __str__(self):
        return 'W_Bool(%s)' % (str(self._boolval_), )

    def ToObject(self):
        from js.object_space import object_space
        return object_space.new_obj(W_BooleanObject, self)

    def to_string(self):
        if self._boolval_ == True:
            return u'true'
        return u'false'

    def ToNumber(self):
        if self._boolval_ == True:
            return 1.0
        return 0.0

    def to_boolean(self):
        return self._boolval_

class W_String(W_Primitive):
    _type_ = 'string'

    def __init__(self, strval):
        assert isinstance(strval, unicode)
        W_Primitive.__init__(self)
        self._strval_ = strval

    def __eq__(self, other):
        other_string = other.to_string()
        return self.to_string() == other_string

    def __str__(self):
        return u'W_String("%s")' % (self._strval_)

    def ToObject(self):
        from js.object_space import object_space
        return object_space.new_obj(W_StringObject, self)

    def to_string(self):
        return self._strval_

    def to_boolean(self):
        if len(self._strval_) == 0:
            return False
        else:
            return True

    def ToNumber(self):
        u_strval = self._strval_
        assert isinstance(u_strval, unicode)

        if u_strval == u'':
            return 0.0
        if u_strval.strip(' ') == u'':
            return 0.0

        strval = str(u_strval)

        try:
            return float(strval)
        except ValueError:
            try:
                return float(int(strval, 16))
            except ValueError:
                try:
                    return float(int(strval, 8))
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
        from js.object_space import object_space
        obj = object_space.new_obj(W_NumericObject, self)
        return obj

    def to_boolean(self):
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

    def __str__(self):
        return 'W_IntNumber(%s)' % (self._intval_,)

    def ToInteger(self):
        return self._intval_

    def ToNumber(self):
        # XXX
        return float(self._intval_)

    def to_string(self):
        # XXX incomplete, this doesn't follow the 9.8.1 recommendation
        return unicode(str(self.ToInteger()))

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

    def __str__(self):
        return 'W_FloatNumber(%s)' % (self._floatval_,)

    def to_string(self):
        # XXX incomplete, this doesn't follow the 9.8.1 recommendation
        if isnan(self._floatval_):
            return u'NaN'
        if isinf(self._floatval_):
            if self._floatval_ > 0:
                return u'Infinity'
            else:
                return u'-Infinity'

        if self._floatval_ == 0:
            return u'0'

        res = u''
        try:
            res = unicode(formatd(self._floatval_, 'g', 10))
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

    def __str__(self):
        return 'W_List(%s)' % ( unicode([unicode(v) for v in self.values]) )

class W_Iterator(W_Root):
    def __init__(self, elements_w):
        self.elements_w = elements_w

    def next(self):
        if self.elements_w:
            return self.elements_w.pop()

    def empty(self):
        return len(self.elements_w) == 0

    def to_string(self):
        return u'<Iterator>'

from pypy.rlib.objectmodel import specialize
@specialize.argtype(0)
def _w(value):
    if isinstance(value, W_Root):
        return value
    elif isinstance(value, bool):
        return newbool(value)
    elif isinstance(value, int) or isinstance(value, long):
        return W_IntNumber(value)
    elif isinstance(value, float):
        return W_FloatNumber(value)
    elif isinstance(value, unicode):
        return W_String(value)
    elif isinstance(value, str):
        return W_String(unicode(value))
    elif isinstance(value, list):
        from js.object_space import object_space
        a = object_space.new_obj(W__Array)
        for index, item in enumerate(value):
            put_property(a, unicode(index), _w(item), writable = True, enumerable = True, configurable = True)
        return a

    elif value is None:
        return w_Null
    raise TypeError(value)

def put_property(obj, name, value, writable = False, configurable = False, enumerable = False, throw = False):
    descriptor = PropertyDescriptor(value = value, writable = writable, configurable = configurable, enumerable = enumerable)
    obj.define_own_property(name, descriptor, throw)
