# encoding: utf-8
from pypy.rpython.lltypesystem import rffi
from pypy.rlib.rarithmetic import intmask, ovfcheck_float_to_int
from pypy.rlib.rfloat import isnan, isinf, NAN, formatd, INFINITY
from js.execution import JsTypeError, JsRangeError

from pypy.rlib.objectmodel import enforceargs
from pypy.rlib import jit

from js.property_descriptor import PropertyDescriptor, DataPropertyDescriptor, AccessorPropertyDescriptor, is_data_descriptor, is_generic_descriptor, is_accessor_descriptor
from js.property import DataProperty, AccessorProperty
from js.object_map import ROOT_MAP


def _new_map():
    return ROOT_MAP


@jit.elidable
def is_array_index(p):
    try:
        return unicode(str(uint32(abs(int(str(p)))))) == p
    except ValueError:
        return False


@jit.elidable
def sign(i):
    if i > 0:
        return 1
    if i < 0:
        return -1
    return 0


class W_Root(object):
    _immutable_fields_ = ['_type_']
    _type_ = ''

    def __str__(self):
        return self.to_string()

    def to_string(self):
        return u''

    def type(self):
        return self._type_

    def to_boolean(self):
        return False

    def ToPrimitive(self, hint=None):
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
            raise Exception('dafuq?')
            return 0

        return int(num)

    def ToInt32(self):
        num = self.ToInteger()
        #if num == NAN or num == INFINITY or num == -INFINITY:
            #return 0

        return int32(num)

    def ToUInt32(self):
        num = self.ToInteger()
        #if num == NAN or num == INFINITY or num == -INFINITY:
            #return 0
        return uint32(num)

    def ToInt16(self):
        num = self.ToInteger()
        #if num == NAN or num == INFINITY or num == -INFINITY or num == 0:
            #return 0

        return uint16(num)

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

    def ToObject(self):
        raise JsTypeError(u'W_Undefined.ToObject')


class W_Null(W_Primitive):
    _type_ = 'null'

    def to_boolean(self):
        return False

    def to_string(self):
        return u'null'

    def check_object_coercible(self):
        raise JsTypeError(u'W_Null.check_object_coercible')

    def ToObject(self):
        raise JsTypeError(u'W_Null.ToObject')

w_Undefined = W_Undefined()
w_Null = W_Null()


class PropertyIdenfidier(object):
    def __init__(self, name, descriptor):
        self.name = name
        self.descriptor = descriptor


class W_ProtoGetter(W_Root):
    def is_callable(self):
        return True

    def Call(self, args=[], this=None, calling_context=None):
        if not isinstance(this, W_BasicObject):
            raise JsTypeError(u'')

        return this._prototype_


class W_ProtoSetter(W_Root):
    def is_callable(self):
        return True

    def Call(self, args=[], this=None, calling_context=None):
        if not isinstance(this, W_BasicObject):
            raise JsTypeError(u'')

        proto = args[0]
        this._prototype_ = proto

w_proto_getter = W_ProtoGetter()
w_proto_setter = W_ProtoSetter()
proto_desc = AccessorPropertyDescriptor(w_proto_getter, w_proto_setter, False, False)
jit.promote(proto_desc)


@jit.elidable
def reject(throw, msg=u''):
    if throw:
        raise JsTypeError(msg)
    return False


class W_BasicObject(W_Root):
    _type_ = 'object'
    _class_ = 'Object'
    _extensible_ = True
    _immutable_fields_ = ['_type_', '_class_', '_extensible_']

    def __init__(self):
        self._property_map_ = _new_map()
        self._property_slots_ = []

        self._prototype_ = w_Null
        W_BasicObject.define_own_property(self, u'__proto__', proto_desc)

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
        assert p is not None and isinstance(p, unicode)
        desc = self.get_property(p)

        if desc is None:
            return w_Undefined

        if is_data_descriptor(desc):
            return desc.value

        getter = desc.getter
        if getter is None:
            return w_Undefined

        res = getter.Call(this=self)
        return res

    # 8.12.1
    def get_own_property(self, p):
        assert p is not None and isinstance(p, unicode)

        prop = self._get_prop(p)
        if prop is None:
            return

        return prop.to_property_descriptor()

    def _get_prop(self, name):
        idx = self._property_map_.lookup(name)

        if self._property_map_.not_found(idx):
            return
        elif idx >= len(self._property_slots_):
                return

        prop = self._property_slots_[idx]
        return prop

    def _del_prop(self, name):
        idx = self._property_map_.lookup(name)

        if self._property_map_.not_found(idx):
            return

        del(self._property_slots_[idx])
        self._property_map_ = self._property_map_.delete(name)

    def _set_prop(self, name, value):
        idx = self._property_map_.lookup(name)

        if self._property_map_.not_found(idx):
            self._property_map_ = self._property_map_.add(name)
            idx = self._property_map_.index

        if idx >= len(self._property_slots_):
            self._property_slots_ += ([None] * (1 + idx - len(self._property_slots_)))

        self._property_slots_[idx] = value

    # 8.12.2
    def get_property(self, p):
        assert p is not None and isinstance(p, unicode)

        prop = self.get_own_property(p)
        if prop is not None:
            return prop

        proto = self.prototype()
        if proto is w_Null:
            return None

        return proto.get_property(p)

    # 8.12.5
    def put(self, p, v, throw=False):
        #assert isinstance(p, unicode)
        assert p is not None and isinstance(p, unicode)

        if self.can_put(p) is False:
            if throw is True:
                raise JsTypeError(u"can't put %s" % (p, ))
            else:
                return

        own_desc = self.get_own_property(p)
        if is_data_descriptor(own_desc) is True:
            value_desc = PropertyDescriptor(value=v)
            self.define_own_property(p, value_desc, throw)
            return

        desc = self.get_property(p)
        if is_accessor_descriptor(desc) is True:
            setter = desc.setter
            assert setter is not None
            setter.Call(this=self, args=[v])
        else:
            new_desc = DataPropertyDescriptor(v, True, True, True)
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
        #assert isinstance(p, unicode)
        assert p is not None and isinstance(p, unicode)

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
            self._del_prop(p)
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
    def define_own_property(self, p, desc, throw=False):
        current = self.get_own_property(p)
        extensible = self.extensible()

        # 3.
        if current is None and extensible is False:
            return reject(throw, p)

        # 4.
        if current is None and extensible is True:
            # 4.a
            if is_generic_descriptor(desc) or is_data_descriptor(desc):
                new_prop = DataProperty(
                    desc.value,
                    desc.writable,
                    desc.enumerable,
                    desc.configurable
                )
                self._set_prop(p, new_prop)
            # 4.b
            else:
                assert is_accessor_descriptor(desc) is True
                new_prop = AccessorProperty(
                    desc.getter,
                    desc.setter,
                    desc.enumerable,
                    desc.configurable
                )
                self._set_prop(p, new_prop)
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
                return reject(throw, p)
            if desc.has_set_enumerable() and (not(current.enumerable) == desc.enumerable):
                return reject(throw, p)

        # 8.
        if is_generic_descriptor(desc):
            pass
        # 9.
        elif is_data_descriptor(current) != is_data_descriptor(desc):
            # 9.a
            if current.configurable is False:
                return reject(throw, p)
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
                    return reject(throw, p)
                # 10.a.ii
                if current.writable is False:
                    if desc.has_set_value() and desc.value != current.value:
                        return reject(throw, p)
            # 10.b
            else:
                pass
        # 11
        elif is_accessor_descriptor(current) and is_accessor_descriptor(desc):
            # 11.a
            if current.configurable is False:
                # 11.a.i
                if desc.has_set_setter() and desc.setter != current.setter:
                    return reject(throw, p)
                # 11.a.ii
                if desc.has_set_getter() and desc.getter != current.getter:
                    return reject(throw, p)
        # 12
        prop = self._get_prop(p)
        self._set_prop(p, prop.update_with_descriptor(desc))

        # 13
        return True

    ##########
    def to_boolean(self):
        return True

    def ToNumber(self):
        return self.ToPrimitive('Number').ToNumber()

    def to_string(self):
        return self.ToPrimitive('String').to_string()

    def ToPrimitive(self, hint=None):
        return self.default_value(hint)

    def ToObject(self):
        return self

    def has_instance(self, other):
        raise JsTypeError(u'has_instance')
    ###

    def _named_properties_dict(self):
        my_d = {}
        for i in self._property_map_.keys():
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
            obj = object_space.new_obj()
            object_space.assign_proto(obj, proto)
        else:
            # would love to test this
            # but I fail to find a case that falls into this
            obj = object_space.new_obj()

        result = self.Call(args, this=obj)
        if isinstance(result, W__Object):
            return result

        return obj

    def is_callable(self):
        return True

    def _to_string_(self):
        return u'function() {}'

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
        obj = object_space.new_obj()
        return obj

    def _to_string_(self):
        return u'function Object() { [native code] }'

    # TODO
    def Construct(self, args=[]):
        return self.Call(args, this=None)

class W_FunctionConstructor(W_BasicFunction):
    def _to_string_(self):
        return u'function Function() { [native code] }'

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
        w_func = object_space.new_func(func, formal_parameter_list = params, scope = scope, strict = strict)
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
        arg0 = get_arg(args, 0, _w(u""))
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
    def Call(self, args = [], this = None, calling_context = None):
        import time
        #from js.builtins import get_arg
        # TODO
        #import datetime

        #if len(args) > 1:
        #    arg0 = get_arg(args, 0);
        #    arg1 = get_arg(args, 1, _w(0));
        #    arg2 = get_arg(args, 2, _w(0));

        #    year = arg0.ToInteger()
        #    month = arg1.ToInteger() + 1
        #    day = arg2.ToInteger() + 1

        #    d = datetime.date(year, month, day)
        #    sec = time.mktime(d.timetuple())
        #    value = _w(int(sec * 1000))

        #elif len(args) == 1:
        #    arg0 = get_arg(args, 0);
        #    if isinstance(arg0, W_String):
        #        raise NotImplementedError()
        #    else:
        #        num = arg0.ToNumber()
        #        if isnan(num) or isinf(num):
        #            raise JsTypeError(unicode(num))
        #        value = _w(int(num))
        #else:
        #    value = _w(int(time.time() * 1000))
        value = _w(int(time.time() * 1000))

        from js.object_space import object_space
        obj = object_space.new_date(value)
        return obj

    # 15.7.2.1
    def Construct(self, args=[]):
        return self.Call(args).ToObject()

    def _to_string_(self):
        return u'function Date() { [native code] }'


class W__Function(W_BasicFunction):

    def __init__(self, function_body, formal_parameter_list=[], scope=None, strict=False):
        W_BasicFunction.__init__(self)
        from js.object_space import object_space
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
        proto_obj = object_space.new_obj()
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
        _map = object_space.new_obj()
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


def make_arg_getter(name, env): pass
    #code = u'return %s;' % (name)


def make_arg_setter(name, env): pass
    #param = u'%s_arg' % (name)
    #code = u'%s = %s;' % (name, param)


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
                array = object_space.new_array(_w(length))
            else:
                length = 1
                array = object_space.new_array(_w(length))
                array.put(u'0', _len)

            return array
        else:
            array = object_space.new_array()
            for index, obj in enumerate(args):
                array.put(unicode(str(index)), obj)
            return array

    def Construct(self, args=[]):
        return self.Call(args)


# 15.8
class W_Math(W__Object):
    _class_ = 'Math'

class W_Boolean(W_Primitive):
    _type_ = 'boolean'
    _immutable_fields_ = ['_boolval_']

    def __init__(self, boolval):
        self._boolval_ = bool(boolval)

    def __str__(self):
        return 'W_Bool(%s)' % (str(self._boolval_), )

    def ToObject(self):
        from js.object_space import object_space
        return object_space.new_bool(self)

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

def _isspace(s):
    whitespace = {u' ':None, u'\n':None, u'\t':None, u'\r':None}
    for i in xrange(len(s)):
        if s[i] not in whitespace:
            return False
    return True


class W_String(W_Primitive):
    _type_ = 'string'
    _immutable_fields_ = ['_strval_']

    def __init__(self, strval):
        assert strval is not None and isinstance(strval, unicode)
        self._strval_ = strval

    def __eq__(self, other):
        other_string = other.to_string()
        return self.to_string() == other_string

    def __str__(self):
        return u'W_String("%s")' % (self._strval_)

    def ToObject(self):
        from js.object_space import object_space
        return object_space.new_string(self)

    def to_string(self):
        return self._strval_

    def to_boolean(self):
        if len(self._strval_) == 0:
            return False
        else:
            return True

    def ToNumber(self):
        from js.builtins_global import _strip
        from runistr import encode_unicode_utf8
        from js.constants import hex_rexp, oct_rexp, num_rexp

        u_strval = self._strval_

        u_strval = _strip(u_strval)
        s = encode_unicode_utf8(u_strval)

        if s == '':
            return 0.0

        match_data = num_rexp.match(s)
        if match_data is not None:
            num_lit = match_data.group()
            assert num_lit is not None
            assert isinstance(num_lit, str)

            if num_lit == 'Infinity' or num_lit == '+Infinity':
                return INFINITY
            elif num_lit == '-Infinity':
                return -INFINITY

            return float(num_lit)

        match_data = hex_rexp.match(s)
        if match_data is not None:
            hex_lit = match_data.group(1)
            assert hex_lit is not None
            assert hex_lit.startswith('0x') is False
            assert hex_lit.startswith('0X') is False
            return int(hex_lit, 16)

        match_data = oct_rexp.match(s)
        if match_data is not None:
            oct_lit = match_data.group(1)
            assert oct_lit is not None
            return int(oct_lit, 8)

        return NAN

class W_Number(W_Primitive):
    """ Base class for numbers, both known to be floats
    and those known to be integers
    """
    _type_ = 'number'

    # 9.9
    def ToObject(self):
        from js.object_space import object_space
        obj = object_space.new_number(self)
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
    _immutable_fields_ = ['_intval_']

    """ Number known to be an integer
    """
    def __init__(self, intval):
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

MASK_32 = (2 ** 32) - 1
MASK_16 = (2 ** 16) - 1

@enforceargs(int)
@jit.elidable
def int32(n):
    if n & (1 << (32 - 1)):
      res = n | ~MASK_32
    else:
      res = n & MASK_32

    return res

@enforceargs(int)
@jit.elidable
def uint32(n):
    return n & MASK_32

@enforceargs(int)
@jit.elidable
def uint16(n):
    return n & MASK_16

class W_FloatNumber(W_Number):
    """ Number known to be a float
    """
    def __init__(self, floatval):
        assert isinstance(floatval, float)
        self._floatval_ = floatval

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
            return int(self._floatval_)

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

w_0 = W_IntNumber(0)


class W__Array(W_BasicObject):
    _class_ = 'Array'

    def __init__(self, length=w_0):
        W_BasicObject.__init__(self)
        assert isinstance(length, W_Root)

        desc = PropertyDescriptor(value=length, writable=True, enumerable=False, configurable=False)
        W_BasicObject.define_own_property(self, u'length', desc)

    # 15.4.5.1
    def define_own_property(self, p, desc, throw=False):
        old_len_desc = self.get_own_property(u'length')
        assert old_len_desc is not None
        old_len = old_len_desc.value.ToUInt32()

        # 3
        if p == u'length':
            if desc.value is None:
                return W_BasicObject.define_own_property(self, u'length', desc, throw)
            new_len_desc = desc.copy()
            new_len = desc.value.ToUInt32()

            if new_len != desc.value.ToNumber():
                raise JsRangeError()

            new_len_desc.value = _w(new_len)

            # f
            if new_len >= old_len:
                return W_BasicObject.define_own_property(self, u'length', new_len_desc, throw)
            # g
            if old_len_desc.writable is False:
                return reject(throw, p)

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
                    return reject(throw, p)

            # m
            if new_writable is False:
                desc = PropertyDescriptor(writable = False)
                res = W_BasicObject.define_own_property(self, u'length', desc, False)
                assert res is True

            return True

        # 4
        elif is_array_index(p):
            #assert isinstance(p, unicode)
            assert p is not None and isinstance(p, unicode)

            # a
            index = uint32(int(p))
            # b
            if index >= old_len and old_len_desc.writable is False:
                return reject(throw, p)

            # c
            succeeded = W_BasicObject.define_own_property(self, p, desc, False)
            # d
            if succeeded is False:
                return reject(throw, p)

            # e
            if index >= old_len:
                old_len_desc.value = _w(index + 1)
                res = W_BasicObject.define_own_property(self, u'length', old_len_desc, False)
                assert res is True
            # f
            return True
        # 5
        return W_BasicObject.define_own_property(self, p, desc, throw)

from pypy.rlib.objectmodel import specialize
@specialize.argtype(0)
def _w(value):
    if value is None:
        return w_Null
    elif isinstance(value, W_Root):
        return value
    elif isinstance(value, bool):
        return newbool(value)
    elif isinstance(value, int):
        return W_IntNumber(value)
    elif isinstance(value, float):
        return W_FloatNumber(value)
    elif isinstance(value, unicode):
        return W_String(value)
    elif isinstance(value, str):
        u_str = unicode(value)
        return W_String(u_str)
    elif isinstance(value, list):
        from js.object_space import object_space
        a = object_space.new_array()
        for index, item in enumerate(value):
            put_property(a, unicode(str(index)), _w(item), writable = True, enumerable = True, configurable = True)
        return a

    raise TypeError, ("ffffuuu %s" % (value,))

def put_property(obj, name, value, writable = False, configurable = False, enumerable = False, throw = False):
    descriptor = PropertyDescriptor(value = value, writable = writable, configurable = configurable, enumerable = enumerable)
    obj.define_own_property(name, descriptor, throw)
