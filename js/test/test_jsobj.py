from js.jsobj import W_BasicObject, PropertyDescriptor


class TestWObjectProperties(object):
    def test_has_property(self):
        obj = W_BasicObject()
        assert obj.has_property(u'foo') is False

    def test_define_property(self):
        obj = W_BasicObject()

        desc = PropertyDescriptor(enumerable=True, configurable=True)
        obj.define_own_property(u'foo', desc)
        assert obj.has_property(u'foo') is True

    def test_define_data_property(self):
        obj = W_BasicObject()

        desc = PropertyDescriptor(value=1)
        obj.define_own_property(u'foo', desc)
        assert obj.has_property(u'foo') is True

    def test_get(self):
        obj = W_BasicObject()

        desc = PropertyDescriptor(value=1, writable=True)
        obj.define_own_property(u'foo', desc)
        assert obj.get(u'foo') == 1

    def test_put(self):
        obj = W_BasicObject()

        obj.put(u'foo', 1)
        assert obj.get(u'foo') == 1

#def test_intnumber():
    #n = W_IntNumber(0x80000000)
    #assert n.ToInt32() == -0x80000000
    #assert n.ToUInt32() == 0x80000000

#def test_floatnumber():
    #n = W_FloatNumber(float(0x80000000))
    #assert n.ToInt32() == -0x80000000
    #assert n.ToUInt32() == 0x80000000

#class TestType(object):
    #def test_undefined(self):
        #assert w_Undefined.type() == 'undefined'

    #def test_null(self):
        #assert w_Null.type() == 'null'

    #def test_boolean(self):
        #assert w_True.type() == 'boolean'
        #assert w_False.type() == 'boolean'

    #def test_number(self):
        #assert W_IntNumber(0).type() == 'number'
        #assert W_FloatNumber(0.0).type() == 'number'
        #assert W_FloatNumber(NAN).type() == 'number'

    #def test_string(self):
        #assert W_String('').type() == 'string'

    #def test_object(self):
        #assert W_Object().type() == 'object'

#class TestToBoolean(object):
    #def test_undefined(self):
        #assert w_Undefined.ToBoolean() == False

    #def test_null(self):
        #assert w_Null.ToBoolean() == False

    #def test_boolean(self):
        #assert w_True.ToBoolean() == True
        #assert w_False.ToBoolean() == False

    #def test_number(self):
        #assert W_IntNumber(0).ToBoolean() == False
        #assert W_IntNumber(1).ToBoolean() == True
        #assert W_FloatNumber(0.0).ToBoolean() == False
        #assert W_FloatNumber(1.0).ToBoolean() == True
        #assert W_FloatNumber(NAN).ToBoolean() == False

    #def test_string(self):
        #assert W_String('').ToBoolean() == False
        #assert W_String('a').ToBoolean() == True

    #def test_object(self):
        #assert W_Object().ToBoolean() == True

#class TestToNumber(object):
    #def test_undefined(self):
        #assert w_Undefined.ToNumber() is NAN

    #def test_null(self):
        #assert w_Null.ToNumber() == 0

    #def test_boolean(self):
        #assert w_True.ToNumber() == 1
        #assert w_False.ToNumber() == 0

    #def test_number(self):
        #assert W_IntNumber(0).ToNumber() == 0
        #assert W_IntNumber(1).ToNumber() == 1
        #assert W_FloatNumber(0.0).ToNumber() == 0
        #assert W_FloatNumber(1.0).ToNumber() == 1.0
        #assert W_FloatNumber(NAN).ToNumber() is NAN

    #def test_string(self):
        #assert W_String('').ToNumber() == 0
        #assert W_String('x').ToNumber() is NAN
        #assert W_String('1').ToNumber() == 1

    #def test_object(self):
        #py.test.skip()
        #W_Object().ToNumber()

#class Testto_string(object):
    #def test_undefined(self):
        #assert w_Undefined.to_string() == 'undefined'

    #def test_null(self):
        #assert w_Null.to_string() == 'null'

    #def test_boolean(self):
        #assert w_True.to_string() == 'true'
        #assert w_False.to_string() == 'false'

    #def test_number(self):
        #assert W_IntNumber(0).to_string() == '0'
        #assert W_IntNumber(1).to_string() == '1'
        #assert W_FloatNumber(0.0).to_string() == '0'
        #assert W_FloatNumber(1.0).to_string() == '1'
        #assert W_FloatNumber(NAN).to_string() == 'NaN'

    #def test_string(self):
        #assert W_String('').to_string() == ''
        #assert W_String('x').to_string() == 'x'
        #assert W_String('1').to_string() == '1'

    #def test_object(self):
        #py.test.skip()
        #W_Object().to_string()

#class TestW_BasicObject(object):
    #def test_Prototype(self):
        #assert W_BasicObject().Prototype() is w_Undefined

    #def test_Class(self):
        #assert W_BasicObject().Class() == 'Object'

#class TestW_BooleanObject(object):
    #def test_toPrimitive(self):
        #py.test.skip()
        #b = W_BooleanObject(w_True)
        #assert b.ToPrimitive() == w_True


##class TestW__Function(object):
    ##def test_Call(self):
        ##from js.jsobj import W__Function, W_List, _w
        ##from js.jscode import Js_NativeFunction
        ##from js.jsexecution_context import make_global_context

        ##ctx = make_global_context()

        ##def f(this, args):
            ##return 1

        ##nf = Js_NativeFunction(f)
        ##f = W__Function(ctx, nf)

        ##assert f.Call([_w(None), _w(None)]).ToInteger() == 1
