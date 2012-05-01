from js.jsobj import W_IntNumber, W_FloatNumber, W_String,\
     w_Undefined, newbool, W__Object, \
     w_True, w_False, w_Null, W_Root, W__Function
import js.jsobj as jsobj
from js.execution import JsTypeError, ReturnException, ThrowException
from js.baseop import plus, sub, compare, AbstractEC, StrictEC,\
     compare_e, increment, decrement, commonnew, mult, division, uminus, mod
from pypy.rlib.rarithmetic import intmask
from pypy.rlib import jit

class Opcode(object):
    _stack_change = 1
    def __init__(self):
        pass

    def eval(self, ctx):
        """ Execute in context ctx
        """
        raise NotImplementedError

    def stack_change(self):
        return self._stack_change

    def __str__(self):
        return self.__class__.__name__

class BaseBinaryComparison(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        s4 = ctx.stack_pop()
        s2 = ctx.stack_pop()
        ctx.stack_append(self.decision(ctx, s2, s4))

    def decision(self, ctx, op1, op2):
        raise NotImplementedError

class BaseBinaryBitwiseOp(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        s5 = ctx.stack_pop().ToInt32()
        s6 = ctx.stack_pop().ToInt32()
        ctx.stack_append(self.operation(ctx, s5, s6))

    def operation(self, ctx, op1, op2):
        raise NotImplementedError

class BaseBinaryOperation(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        right = ctx.stack_pop()
        left = ctx.stack_pop()
        ctx.stack_append(self.operation(ctx, left, right))

class BaseUnaryOperation(Opcode):
    _stack_change = 0

class Undefined(Opcode):
    def eval(self, ctx):
        ctx.stack_append(w_Undefined)

class LOAD_INTCONSTANT(Opcode):
    _immutable_fields_ = ['w_intvalue']
    def __init__(self, value):
        self.w_intvalue = W_IntNumber(int(value))

    def eval(self, ctx):
        ctx.stack_append(self.w_intvalue)

    #def __repr__(self):
        #return 'LOAD_INTCONSTANT %s' % (self.w_intvalue.ToInteger(),)

class LOAD_BOOLCONSTANT(Opcode):
    def __init__(self, value):
        self.boolval = value

    def eval(self, ctx):
        ctx.stack_append(newbool(self.boolval))

class LOAD_FLOATCONSTANT(Opcode):
    def __init__(self, value):
        self.w_floatvalue = W_FloatNumber(float(value))

    def eval(self, ctx):
        ctx.stack_append(self.w_floatvalue)

    #def __repr__(self):
        #return 'LOAD_FLOATCONSTANT %s' % (self.w_floatvalue.ToNumber(),)

class LOAD_STRINGCONSTANT(Opcode):
    _immutable_fields_ = ['w_stringvalue']
    def __init__(self, value):
        self.w_stringvalue = W_String(value)

    def eval(self, ctx):
        ctx.stack_append(self.w_stringvalue)

    #def __repr__(self):
        #return 'LOAD_STRINGCONSTANT "%s"' % (self.w_stringvalue.ToString(),)

class LOAD_UNDEFINED(Opcode):
    def eval(self, ctx):
        ctx.stack_append(w_Undefined)

class LOAD_NULL(Opcode):
    def eval(self, ctx):
        ctx.stack_append(w_Null)

class LOAD_VARIABLE(Opcode):
    #_immutable_fields_ = ['identifier']
    def __init__(self, index):
        assert index is not None
        self.index = index

    # 11.1.2
    def eval(self, ctx):
        # TODO put ref onto stack
        ref = ctx.get_ref(self.index)
        value = ref.get_value()
        ctx.stack_append(value)

class LOAD_THIS(Opcode):
    # 11.1.1
    def eval(self, ctx):
        this = ctx.this_binding()
        ctx.stack_append(this)

class LOAD_ARRAY(Opcode):
    def __init__(self, counter):
        self.counter = counter

    def eval(self, ctx):
        from js.jsobj import W__Array
        array = W__Array()
        for i in range(self.counter):
            array.Put(str(self.counter - i - 1), ctx.stack_pop())
        ctx.stack_append(array)

    def stack_change(self):
        return -1 * self.counter + 1

    #def __repr__(self):
        #return 'LOAD_ARRAY %d' % (self.counter,)

class LOAD_LIST(Opcode):
    _immutable_fields_ = ['counter']
    def __init__(self, counter):
        self.counter = counter

    def eval(self, ctx):
        from js.jsobj import W_List
        list_w = ctx.stack_pop_n(self.counter) # [:] # pop_n returns a non-resizable list
        ctx.stack_append(W_List(list_w))

    def stack_change(self):
        return -1 * self.counter + 1

    #def __repr__(self):
        #return 'LOAD_LIST %d' % (self.counter,)

class LOAD_FUNCTION(Opcode):
    def __init__(self, funcobj):
        self.funcobj = funcobj

    def eval(self, ctx):
        #proto = ctx.get_global().Get('Function').Get('prototype')
        #from js.builtins import get_builtin_prototype
        #proto = get_builtin_prototype('Function')
        scope = ctx.lexical_environment()
        w_func = W__Function(self.funcobj, scope)
        #w_func = W_CallableObject(ctx, proto, self.funcobj)
        #w_func.Put('length', W_IntNumber(len(self.funcobj.params)))
        #w_obj = create_object('Object')
        #w_obj.Put('constructor', w_func, flags = jsobj.DONT_ENUM)
        #w_func.Put('prototype', w_obj)
        ctx.stack_append(w_func)

    #def __repr__(self):
        #return 'LOAD_FUNCTION' # XXX

class LOAD_OBJECT(Opcode):
    _immutable_fields_ = ["counter"]
    def __init__(self, counter):
        self.counter = counter

    @jit.unroll_safe
    def eval(self, ctx):
        w_obj = W__Object()
        for _ in range(self.counter):
            name = ctx.stack_pop().ToString()
            w_elem = ctx.stack_pop()
            w_obj.Put(name, w_elem)
        ctx.stack_append(w_obj)

    #def __repr__(self):
        #return 'LOAD_OBJECT %d' % (self.counter,)

class LOAD_MEMBER(Opcode):
    _stack_change = -1
    def eval(self, ctx):
        w_obj = ctx.stack_pop().ToObject()
        name = ctx.stack_pop().ToString()
        value = w_obj.get(name)
        ctx.stack_append(value)

class COMMA(BaseUnaryOperation):
    def eval(self, ctx):
        one = ctx.stack_pop()
        ctx.stack_pop()
        ctx.stack_append(one)
        # XXX

class SUB(BaseBinaryOperation):
    def operation(self, ctx, left, right):
        return sub(ctx, left, right)

class IN(BaseBinaryOperation):
    def operation(self, ctx, left, right):
        from js.jsobj import W_BasicObject
        if not isinstance(right, W_BasicObject):
            raise ThrowException(W_String("TypeError: "+ repr(right)))
        name = left.ToString()
        return newbool(right.HasProperty(name))

class TYPEOF(BaseUnaryOperation):
    def eval(self, ctx):
        one = ctx.stack_pop()
        ctx.stack_append(W_String(one.type()))

class TYPEOF_VARIABLE(Opcode):
    def __init__(self, name):
        self.name = name

    def eval(self, ctx):
        try:
            var = ctx.resolve_identifier(self.name)
            ctx.stack_append(W_String(var.type()))
        except ThrowException:
            ctx.stack_append(W_String('undefined'))

#class Typeof(UnaryOp):
#    def eval(self, ctx):
#        val = self.expr.eval(ctx)
#        if isinstance(val, W_Reference) and val.GetBase() is None:
#            return W_String("undefined")
#        return W_String(val.GetValue().type())

class ADD(BaseBinaryOperation):
    def operation(self, ctx, left, right):
        return plus(ctx, left, right)

class BITAND(BaseBinaryBitwiseOp):
    def operation(self, ctx, op1, op2):
        return W_IntNumber(op1&op2)

class BITXOR(BaseBinaryBitwiseOp):
    def operation(self, ctx, op1, op2):
        return W_IntNumber(op1^op2)

class BITOR(BaseBinaryBitwiseOp):
    def operation(self, ctx, op1, op2):
        return W_IntNumber(op1|op2)

class BITNOT(BaseUnaryOperation):
    def eval(self, ctx):
        op = ctx.stack_pop().ToInt32()
        ctx.stack_append(W_IntNumber(~op))

class URSH(BaseBinaryBitwiseOp):
    def eval(self, ctx):
        op2 = ctx.stack_pop().ToUInt32()
        op1 = ctx.stack_pop().ToUInt32()
        # XXX check if it could fit into int
        f = float(op1 >> (op2 & 0x1F))
        ctx.stack_append(W_FloatNumber(f))

class RSH(BaseBinaryBitwiseOp):
    def eval(self, ctx):
        op2 = ctx.stack_pop().ToUInt32()
        op1 = ctx.stack_pop().ToInt32()
        ctx.stack_append(W_IntNumber(op1 >> intmask(op2 & 0x1F)))

class LSH(BaseBinaryBitwiseOp):
    def eval(self, ctx):
        op2 = ctx.stack_pop().ToUInt32()
        op1 = ctx.stack_pop().ToInt32()
        ctx.stack_append(W_IntNumber(op1 << intmask(op2 & 0x1F)))

class MUL(BaseBinaryOperation):
    def operation(self, ctx, op1, op2):
        return mult(ctx, op1, op2)

class DIV(BaseBinaryOperation):
    def operation(self, ctx, op1, op2):
        return division(ctx, op1, op2)

class MOD(BaseBinaryOperation):
    def operation(self, ctx, op1, op2):
        return mod(ctx, op1, op2)

class UPLUS(BaseUnaryOperation):
    def eval(self, ctx):
        if isinstance(ctx.stack_top(), W_IntNumber):
            return
        if isinstance(ctx.stack_top(), W_FloatNumber):
            return
        ctx.stack_append(W_FloatNumber(ctx.stack_pop().ToNumber()))

class UMINUS(BaseUnaryOperation):
    def eval(self, ctx):
        ctx.stack_append(uminus(ctx.stack_pop(), ctx))

class NOT(BaseUnaryOperation):
    def eval(self, ctx):
        ctx.stack_append(newbool(not ctx.stack_pop().ToBoolean()))

class INCR(BaseUnaryOperation):
    def eval(self, ctx):
        value = ctx.stack_pop()
        newvalue = increment(ctx, value)
        ctx.stack_append(newvalue)

class DECR(BaseUnaryOperation):
    def eval(self, ctx):
        value = ctx.stack_pop()
        newvalue = decrement(ctx, value)
        ctx.stack_append(newvalue)

class GT(BaseBinaryComparison):
    def decision(self, ctx, op1, op2):
        return newbool(compare(ctx, op1, op2))

class GE(BaseBinaryComparison):
    def decision(self, ctx, op1, op2):
        return newbool(compare_e(ctx, op1, op2))

class LT(BaseBinaryComparison):
    def decision(self, ctx, op1, op2):
        return newbool(compare(ctx, op2, op1))

class LE(BaseBinaryComparison):
    def decision(self, ctx, op1, op2):
        return newbool(compare_e(ctx, op2, op1))

class EQ(BaseBinaryComparison):
    def decision(self, ctx, op1, op2):
        return newbool(AbstractEC(ctx, op1, op2))

class NE(BaseBinaryComparison):
    def decision(self, ctx, op1, op2):
        return newbool(not AbstractEC(ctx, op1, op2))

class IS(BaseBinaryComparison):
    def decision(self, ctx, op1, op2):
        return newbool(StrictEC(ctx, op1, op2))

class ISNOT(BaseBinaryComparison):
    def decision(self, ctx, op1, op2):
        return newbool(not StrictEC(ctx, op1, op2))

class STORE_MEMBER(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        left = ctx.stack_pop()
        member = ctx.stack_pop()
        value = ctx.stack_pop()
        name = member.ToString()
        left.ToObject().Put(name, value)
        ctx.stack_append(value)

class STORE(Opcode):
    #_immutable_fields_ = ['name']
    _stack_change = 0
    def __init__(self, index):
        assert index is not None
        self.index = index

    def eval(self, ctx):
        value = ctx.stack_top()
        ref = ctx.get_ref(self.index)
        ref.put_value(value)


class LABEL(Opcode):
    _stack_change = 0
    def __init__(self, num):
        self.num = num

    #def __repr__(self):
        #return 'LABEL %d' % (self.num,)

class BaseJump(Opcode):
    _immutable_fields_ = ['where']
    _stack_change = 0
    def __init__(self, where):
        self.where = where
        self.decision = False

    def do_jump(self, ctx, pos):
        return 0

    #def __repr__(self):
        #return '%s %d' % (self.__class__.__name__, self.where)

class JUMP(BaseJump):
    def eval(self, ctx):
        pass

    def do_jump(self, ctx, pos):
        return self.where

class BaseIfJump(BaseJump):
    def eval(self, ctx):
        value = ctx.stack_pop()
        self.decision = value.ToBoolean()

class BaseIfNopopJump(BaseJump):
    def eval(self, ctx):
        value = ctx.stack_top()
        self.decision = value.ToBoolean()

class JUMP_IF_FALSE(BaseIfJump):
    def do_jump(self, ctx, pos):
        if self.decision:
            return pos + 1
        return self.where

class JUMP_IF_FALSE_NOPOP(BaseIfNopopJump):
    def do_jump(self, ctx, pos):
        if self.decision:
            ctx.stack_pop()
            return pos + 1
        return self.where

class JUMP_IF_TRUE(BaseIfJump):
    def do_jump(self, ctx, pos):
        if self.decision:
            return self.where
        return pos + 1

class JUMP_IF_TRUE_NOPOP(BaseIfNopopJump):
    def do_jump(self, ctx, pos):
        if self.decision:
            return self.where
        ctx.stack_pop()
        return pos + 1

class DECLARE_FUNCTION(Opcode):
    _stack_change = 0
    def __init__(self, funcobj):
        self.funcobj = funcobj

    def eval(self, ctx):
        pass
        #from js.jsobj import DONT_ENUM, READ_ONLY
        ## 13.2 Creating Function Objects
        ## TODO move this to W__Function.__init__ ?

        #func = W__Function(ctx, self.funcobj)

        #func.Put('length', W_IntNumber(len(self.funcobj.params())), flags = DONT_ENUM | READ_ONLY)

        #proto = W__Object()
        #proto.Put('constructor', func, flags = DONT_ENUM)

        #func.Put('prototype', proto, flags = DONT_ENUM)

        #ctx.stack_append(funcobj)

        #if self.funcobj.name is not None:
            #ctx.set_value(self.funcobj.name, func)

    def __str__(self):
        funcobj = self.funcobj
        if funcobj.name is None:
            name = ""
        else:
            name = funcobj.name + " "
        return 'DECLARE_FUNCTION %s%r' % (name, funcobj.params)

    ##def __repr__(self):
    ##    funcobj = self.funcobj
    ##    if funcobj.name is None:
    ##        name = ""
    ##    else:
    ##        name = funcobj.name + " "
    ##    codestr = '\n'.join(['  %r' % (op,) for op in funcobj.opcodes])
    ##    ##return 'DECLARE_FUNCTION %s%r [\n%s\n]' % (name, funcobj.params, codestr)
    ##    return 'DECLARE_FUNCTION %s%r' % (name, funcobj.params)

class DECLARE_VAR(Opcode):
    _stack_change = 0
    def __init__(self, name):
        self.name = name

    def eval(self, ctx):
        pass
        #ctx.declare_variable(self.name)

    #def __repr__(self):
        #return 'DECLARE_VAR "%s"' % (self.name,)

class RETURN(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        pass
        #raise ReturnException(ctx.stack_pop())

class POP(Opcode):
    _stack_change = -1
    def eval(self, ctx):
        ctx.stack_pop()

def common_call(ctx, r1, args, this, name):
    # TODO
    from js.jsobj import W_BasicFunction, W_BasicObject
    if not (isinstance(r1, W_BasicFunction) or isinstance(r1, W_BasicObject)):
        raise ThrowException(W_String("%s is not a callable (%s)"%(r1.ToString(), name.ToString())))
    jit.promote(r1)
    try:
        res = r1.Call(args.ToList(), this)
    except JsTypeError:
        raise ThrowException(W_String("%s is not a function (%s)"%(r1.ToString(), name.ToString())))
    return res

class CALL(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        r1 = ctx.stack_pop()
        args = ctx.stack_pop()
        this = ctx.this_binding()
        ctx.stack_append(common_call(ctx, r1, args, this, r1))

class CALL_METHOD(Opcode):
    _stack_change = -2
    def eval(self, ctx):
        method = ctx.stack_pop()
        what = ctx.stack_pop().ToObject()
        args = ctx.stack_pop()
        name = method.ToString()
        r1 = what.Get(name)
        ctx.stack_append(common_call(ctx, r1, args, what, method))

class DUP(Opcode):
    def eval(self, ctx):
        ctx.stack_append(ctx.stack_top())

class THROW(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        val = ctx.stack_pop()
        raise ThrowException(val)

class TRYCATCHBLOCK(Opcode):
    _stack_change = 0
    def __init__(self, tryfunc, catchparam, catchfunc, finallyfunc):
        self.tryfunc     = tryfunc
        self.catchfunc   = catchfunc
        self.catchparam  = catchparam
        self.finallyfunc = finallyfunc

    def eval(self, ctx):
        try:
            try:
                self.tryfunc.run(ctx)
            except ThrowException, e:
                if self.catchfunc is not None:
                    # XXX just copied, I don't know if it's right
                    from js.jsexecution_context import make_catch_context
                    newctx = make_catch_context(ctx, self.catchparam, e.exception)
                    self.catchfunc.run(newctx)
                if self.finallyfunc is not None:
                    self.finallyfunc.run(ctx)
                if not self.catchfunc:
                    raise
        except ReturnException:
            # we run finally block here and re-raise the exception
            if self.finallyfunc is not None:
                self.finallyfunc.run(ctx)
            raise

    #def __repr__(self):
        #return "TRYCATCHBLOCK" # XXX shall we add stuff here???

class NEW(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        y = ctx.stack_pop()
        x = ctx.stack_pop()
        assert isinstance(y, W_List)
        args = y.get_args()
        ctx.stack_append(commonnew(ctx, x, args))

class NEW_NO_ARGS(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        x = ctx.stack_pop()
        ctx.stack_append(commonnew(ctx, x, []))

# ------------ iterator support ----------------

class LOAD_ITERATOR(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        obj = ctx.stack_pop().ToObject()
        props = []
        from js.jsobj import W_BasicObject
        assert isinstance(obj, W_BasicObject)

        for prop in obj._get_property_keys():
            if not obj._get_property_flags(prop) & jsobj.DONT_ENUM:
                props.append(obj._get_property_value(prop))

        ctx.stack_append(W_Iterator(props))

class JUMP_IF_ITERATOR_EMPTY(BaseJump):
    def eval(self, ctx):
        pass

    def do_jump(self, ctx, pos):
        iterator = ctx.stack_top()
        assert isinstance(iterator, W_Iterator)
        if iterator.empty():
            return self.where
        return pos + 1

class NEXT_ITERATOR(Opcode):
    _stack_change = 0
    def __init__(self, name):
        self.name = name

    def eval(self, ctx):
        iterator = ctx.stack_top()
        assert isinstance(iterator, W_Iterator)
        ctx.assign(self.name, iterator.next())

# ---------------- with support ---------------------

class WITH_START(Opcode):
    _stack_change = 0
    def __init__(self):
        self.newctx = None

    def eval(self, ctx):
        obj = ctx.stack_pop().ToObject()
        from js.jsexecution_context import make_with_context
        self.newctx = make_with_context(ctx, obj)

class WITH_END(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        ctx = ctx.parent

# ------------------ delete -------------------------

class DELETE(Opcode):
    def __init__(self, name):
        self.name = name

    def eval(self, ctx):
        ctx.stack_append(newbool(ctx.delete_identifier(self.name)))

class DELETE_MEMBER(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        what = ctx.stack_pop().ToString()
        obj = ctx.stack_pop().ToObject()
        ctx.stack_append(newbool(obj.Delete(what)))

class LOAD_LOCAL(Opcode):
    _immutable_fields_ = ['local']
    def __init__(self, local):
        self.local = local

    def eval(self, ctx):
        ctx.stack_append(ctx.get_local_value(self.local))

    #def __repr__(self):
        #return 'LOAD_LOCAL %d' % (self.local,)

class STORE_LOCAL(Opcode):
    _stack_change = 0
    _immutable_fields_ = ['local']
    def __init__(self, local):
        self.local = local

    def eval(self, ctx):
        value = ctx.stack_top()
        ctx.assign_local(self.local, value)

    #def __repr__(self):
        #return 'STORE_LOCAL %d' % (self.local,)

# different opcode mappings, to make annotator happy

OpcodeMap = {}

for name, value in locals().items():
    if name.upper() == name and type(value) == type(Opcode) and issubclass(value, Opcode):
        OpcodeMap[name] = value

class Opcodes:
    pass

opcodes = Opcodes()
for name, value in OpcodeMap.items():
    setattr(opcodes, name, value)
