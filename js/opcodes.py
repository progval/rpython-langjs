from js.jsobj import W_IntNumber, W_FloatNumber, W_String,\
     W_Array, W_PrimitiveObject, ActivationObject,\
     create_object, W_Object, w_Undefined, newbool,\
     w_True, w_False, W_List, w_Null, W_Iterator, W_Root
import js.jsobj as jsobj
from js.execution import JsTypeError, ReturnException, ThrowException
from pypy.rlib.unroll import unrolling_iterable
from js.baseop import plus, sub, compare, AbstractEC, StrictEC,\
     compare_e, increment, decrement, commonnew, mult, division, uminus, mod
from pypy.rlib.rarithmetic import intmask

class Opcode(object):
    def __init__(self):
        pass

    def eval(self, ctx, stack):
        """ Execute in context ctx
        """
        raise NotImplementedError

    def __repr__(self):
        return self.__class__.__name__

class BaseBinaryComparison(Opcode):
    def eval(self, ctx, stack):
        s4 = stack.pop()
        s2 = stack.pop()
        stack.append(self.decision(ctx, s2, s4))

    def decision(self, ctx, op1, op2):
        raise NotImplementedError

class BaseBinaryBitwiseOp(Opcode):
    def eval(self, ctx, stack):
        s5 = stack.pop().ToInt32(ctx)
        s6 = stack.pop().ToInt32(ctx)
        stack.append(self.operation(ctx, s5, s6))

    def operation(self, ctx, op1, op2):
        raise NotImplementedError

class BaseBinaryOperation(Opcode):
    def eval(self, ctx, stack):
        right = stack.pop()
        left = stack.pop()
        stack.append(self.operation(ctx, left, right))

class BaseUnaryOperation(Opcode):
    pass

class Undefined(Opcode):
    def eval(self, ctx, stack):
        stack.append(w_Undefined)

class LOAD_INTCONSTANT(Opcode):
    _immutable_fields_ = ['w_intvalue']
    def __init__(self, value):
        self.w_intvalue = W_IntNumber(int(value))

    def eval(self, ctx, stack):
        stack.append(self.w_intvalue)

    def __repr__(self):
        return 'LOAD_INTCONSTANT %s' % (self.w_intvalue.intval,)

class LOAD_BOOLCONSTANT(Opcode):
    def __init__(self, value):
        self.boolval = value

    def eval(self, ctx, stack):
        stack.append(newbool(self.boolval))

class LOAD_FLOATCONSTANT(Opcode):
    def __init__(self, value):
        self.w_floatvalue = W_FloatNumber(float(value))

    def eval(self, ctx, stack):
        stack.append(self.w_floatvalue)

    def __repr__(self):
        return 'LOAD_FLOATCONSTANT %s' % (self.w_floatvalue.floatval,)

class LOAD_STRINGCONSTANT(Opcode):
    def __init__(self, value):
        self.w_stringvalue = W_String(value)

    def eval(self, ctx, stack):
        stack.append(self.w_stringvalue)

    #def get_literal(self, ctx):
    #    return W_String(self.strval).ToString(ctx)

    def __repr__(self):
        return 'LOAD_STRINGCONSTANT "%s"' % (self.w_stringvalue.strval,)

class LOAD_UNDEFINED(Opcode):
    def eval(self, ctx, stack):
        stack.append(w_Undefined)

class LOAD_NULL(Opcode):
    def eval(self, ctx, stack):
        stack.append(w_Null)

class LOAD_VARIABLE(Opcode):
    _immutable_fields_ = ['identifier']
    def __init__(self, identifier):
        self.identifier = identifier

    def eval(self, ctx, stack):
        stack.append(ctx.resolve_identifier(ctx, self.identifier))

    def __repr__(self):
        return 'LOAD_VARIABLE "%s"' % (self.identifier,)

class LOAD_REALVAR(Opcode):
    def __init__(self, depth, identifier):
        self.depth = depth
        self.identifier = identifier

    def eval(self, ctx, stack):
        raise NotImplementedError()
        # XXX
        # scope = ctx.scope[self.depth]
        # stack.append(scope.Get(ctx, self.identifier))
        #stack.append(W_Reference(self.identifier, scope))

    def __repr__(self):
        return 'LOAD_VARIABLE "%s"' % (self.identifier,)

class LOAD_ARRAY(Opcode):
    def __init__(self, counter):
        self.counter = counter

    def eval(self, ctx, stack):
        proto = ctx.get_global().Get(ctx, 'Array').Get(ctx, 'prototype')
        array = W_Array(ctx, Prototype=proto, Class = proto.Class)
        for i in range(self.counter):
            array.Put(ctx, str(self.counter - i - 1), stack.pop())
        stack.append(array)

    def __repr__(self):
        return 'LOAD_ARRAY %d' % (self.counter,)

class LOAD_LIST(Opcode):
    def __init__(self, counter):
        self.counter = counter

    def eval(self, ctx, stack):
        list_w = stack.pop_n(self.counter)
        stack.append(W_List(list_w))

    def __repr__(self):
        return 'LOAD_LIST %d' % (self.counter,)

class LOAD_FUNCTION(Opcode):
    def __init__(self, funcobj):
        self.funcobj = funcobj

    def eval(self, ctx, stack):
        proto = ctx.get_global().Get(ctx, 'Function').Get(ctx, 'prototype')
        w_func = W_Object(ctx=ctx, Prototype=proto, Class='Function',
                          callfunc=self.funcobj)
        w_func.Put(ctx, 'length', W_IntNumber(len(self.funcobj.params)))
        w_obj = create_object(ctx, 'Object')
        w_obj.Put(ctx, 'constructor', w_func, flags = jsobj.DE)
        w_func.Put(ctx, 'prototype', w_obj)
        stack.append(w_func)

    def __repr__(self):
        return 'LOAD_FUNCTION' # XXX

# class STORE_VAR(Opcode):
#     def __init__(self, depth, name):
#         self.name = name
#         self.depth = depth

#     def eval(self, ctx, stack):
#         value = stack[-1]
#         ctx.scope[self.depth].Put(ctx, self.name, value)

#     def __repr__(self):
#         return 'STORE_VAR "%s"' % self.name

class LOAD_OBJECT(Opcode):
    def __init__(self, counter):
        self.counter = counter

    def eval(self, ctx, stack):
        w_obj = create_object(ctx, 'Object')
        for _ in range(self.counter):
            name = stack.pop().ToString(ctx)
            w_elem = stack.pop()
            w_obj.Put(ctx, name, w_elem)
        stack.append(w_obj)

    def __repr__(self):
        return 'LOAD_OBJECT %d' % (self.counter,)

class LOAD_MEMBER(Opcode):
    def eval(self, ctx, stack):
        w_obj = stack.pop().ToObject(ctx)
        name = stack.pop().ToString(ctx)
        stack.append(w_obj.Get(ctx, name))

class COMMA(BaseUnaryOperation):
    def eval(self, ctx, stack):
        one = stack.pop()
        stack.pop()
        stack.append(one)
        # XXX

class SUB(BaseBinaryOperation):
    def operation(self, ctx, left, right):
        return sub(ctx, left, right)

class IN(BaseBinaryOperation):
    def operation(self, ctx, left, right):
        if not isinstance(right, W_Object):
            raise ThrowException(W_String("TypeError"))
        name = left.ToString(ctx)
        return newbool(right.HasProperty(name))

class TYPEOF(BaseUnaryOperation):
    def eval(self, ctx, stack):
        one = stack.pop()
        stack.append(W_String(one.type()))

class TYPEOF_VARIABLE(Opcode):
    def __init__(self, name):
        self.name = name

    def eval(self, ctx, stack):
        try:
            var = ctx.resolve_identifier(ctx, self.name)
            stack.append(W_String(var.type()))
        except ThrowException:
            stack.append(W_String('undefined'))

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
    def eval(self, ctx, stack):
        op = stack.pop().ToInt32(ctx)
        stack.append(W_IntNumber(~op))

class URSH(BaseBinaryBitwiseOp):
    def eval(self, ctx, stack):
        op2 = stack.pop().ToUInt32(ctx)
        op1 = stack.pop().ToUInt32(ctx)
        # XXX check if it could fit into int
        stack.append(W_FloatNumber(op1 >> (op2 & 0x1F)))

class RSH(BaseBinaryBitwiseOp):
    def eval(self, ctx, stack):
        op2 = stack.pop().ToUInt32(ctx)
        op1 = stack.pop().ToInt32(ctx)
        stack.append(W_IntNumber(op1 >> intmask(op2 & 0x1F)))

class LSH(BaseBinaryBitwiseOp):
    def eval(self, ctx, stack):
        op2 = stack.pop().ToUInt32(ctx)
        op1 = stack.pop().ToInt32(ctx)
        stack.append(W_IntNumber(op1 << intmask(op2 & 0x1F)))

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
    def eval(self, ctx, stack):
        if isinstance(stack.top(), W_IntNumber):
            return
        if isinstance(stack.top(), W_FloatNumber):
            return
        stack.append(W_FloatNumber(stack.pop().ToNumber(ctx)))

class UMINUS(BaseUnaryOperation):
    def eval(self, ctx, stack):
        stack.append(uminus(stack.pop(), ctx))

class NOT(BaseUnaryOperation):
    def eval(self, ctx, stack):
        stack.append(newbool(not stack.pop().ToBoolean()))

class INCR(BaseUnaryOperation):
    def eval(self, ctx, stack):
        value = stack.pop()
        newvalue = increment(ctx, value)
        stack.append(newvalue)

class DECR(BaseUnaryOperation):
    def eval(self, ctx, stack):
        value = stack.pop()
        newvalue = decrement(ctx, value)
        stack.append(newvalue)

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
    def eval(self, ctx, stack):
        left = stack.pop()
        member = stack.pop()
        value = stack.pop()
        name = member.ToString(ctx)
        left.ToObject(ctx).Put(ctx, name, value)
        stack.append(value)

class STORE(Opcode):
    _immutable_fields_ = ['name']
    def __init__(self, name):
        self.name = name

    def eval(self, ctx, stack):
        value = stack.top()
        ctx.assign(self.name, value)

    def __repr__(self):
        return '%s "%s"' % (self.__class__.__name__, self.name)

class LABEL(Opcode):
    def __init__(self, num):
        self.num = num

    def __repr__(self):
        return 'LABEL %d' % (self.num,)

class BaseJump(Opcode):
    _immutable_fields_ = ['where']
    def __init__(self, where):
        self.where = where
        self.decision = False

    def do_jump(self, stack, pos):
        return 0

    def __repr__(self):
        return '%s %d' % (self.__class__.__name__, self.where)

class JUMP(BaseJump):
    def eval(self, ctx, stack):
        pass

    def do_jump(self, stack, pos):
        return self.where

class BaseIfJump(BaseJump):
    def eval(self, ctx, stack):
        value = stack.pop()
        self.decision = value.ToBoolean()

class BaseIfNopopJump(BaseJump):
    def eval(self, ctx, stack):
        value = stack.top()
        self.decision = value.ToBoolean()

class JUMP_IF_FALSE(BaseIfJump):
    def do_jump(self, stack, pos):
        if self.decision:
            return pos + 1
        return self.where

class JUMP_IF_FALSE_NOPOP(BaseIfNopopJump):
    def do_jump(self, stack, pos):
        if self.decision:
            stack.pop()
            return pos + 1
        return self.where

class JUMP_IF_TRUE(BaseIfJump):
    def do_jump(self, stack, pos):
        if self.decision:
            return self.where
        return pos + 1

class JUMP_IF_TRUE_NOPOP(BaseIfNopopJump):
    def do_jump(self, stack, pos):
        if self.decision:
            return self.where
        stack.pop()
        return pos + 1

class DECLARE_FUNCTION(Opcode):
    def __init__(self, funcobj):
        self.funcobj = funcobj

    def eval(self, ctx, stack):
        # function declaration actyally don't run anything
        proto = ctx.get_global().Get(ctx, 'Function').Get(ctx, 'prototype')
        w_func = W_Object(ctx=ctx, Prototype=proto, Class='Function', callfunc=self.funcobj)
        w_func.Put(ctx, 'length', W_IntNumber(len(self.funcobj.params)))
        w_obj = create_object(ctx, 'Object')
        w_obj.Put(ctx, 'constructor', w_func, flags = jsobj.DE)
        w_func.Put(ctx, 'prototype', w_obj)
        if self.funcobj.name is not None:
            ctx.scope[-1].Put(ctx, self.funcobj.name, w_func)

    def __repr__(self):
        funcobj = self.funcobj
        if funcobj.name is None:
            name = ""
        else:
            name = funcobj.name + " "
        codestr = '\n'.join(['  %r' % (op,) for op in funcobj.opcodes])
        return 'DECLARE_FUNCTION %s%r [\n%s\n]' % (name, funcobj.params, codestr)

class DECLARE_VAR(Opcode):
    def __init__(self, name):
        self.name = name

    def eval(self, ctx, stack):
        ctx.scope[-1].Put(ctx, self.name, w_Undefined, flags = jsobj.DD)

    def __repr__(self):
        return 'DECLARE_VAR "%s"' % (self.name,)

class RETURN(Opcode):
    def eval(self, ctx, stack):
        raise ReturnException(stack.pop())

class POP(Opcode):
    def eval(self, ctx, stack):
        stack.pop()

def common_call(ctx, r1, args, this, name):
    if not isinstance(r1, W_PrimitiveObject):
        raise ThrowException(W_String("%s is not a callable (%s)"%(r1.ToString(ctx), name)))
    try:
        res = r1.Call(ctx=ctx, args=args.tolist(), this=this)
    except JsTypeError:
        raise ThrowException(W_String("%s is not a function (%s)"%(r1.ToString(ctx), name)))
    return res

class CALL(Opcode):
    def eval(self, ctx, stack):
        r1 = stack.pop()
        args = stack.pop()
        name = r1.ToString(ctx)
        #XXX hack, this should be comming from context
        stack.append(common_call(ctx, r1, args, ctx.scope[-1], name))

class CALL_METHOD(Opcode):
    def eval(self, ctx, stack):
        method = stack.pop()
        what = stack.pop().ToObject(ctx)
        args = stack.pop()
        name = method.ToString(ctx)
        r1 = what.Get(ctx, name)
        stack.append(common_call(ctx, r1, args, what, name))

#class CALL_BASEOP(Opcode):
    #def __init__(self, baseop):
        #self.baseop = baseop

    #def eval(self, ctx, stack):
        #from js.baseop import get_baseop_func
        #func = get_baseop_func(self.baseop)
        #args = stack.pop_n(func.argcount)
        #kwargs = {'ctx':ctx}
        #val = func(*args, **kwargs)
        #stack.append(val)

    #def __repr__(self):
        #from js.baseop import get_baseop_name, get_baseop_func
        #return "CALL_BASEOP %s (%d)" % (get_baseop_name(self.baseop), self.baseop)

class DUP(Opcode):
    def eval(self, ctx, stack):
        stack.append(stack.top())

class THROW(Opcode):
    def eval(self, ctx, stack):
        val = stack.pop()
        raise ThrowException(val)

class TRYCATCHBLOCK(Opcode):
    def __init__(self, tryfunc, catchparam, catchfunc, finallyfunc):
        self.tryfunc     = tryfunc
        self.catchfunc   = catchfunc
        self.catchparam  = catchparam
        self.finallyfunc = finallyfunc

    def eval(self, ctx, stack):
        try:
            try:
                self.tryfunc.run(ctx)
            except ThrowException, e:
                if self.catchfunc is not None:
                    # XXX just copied, I don't know if it's right
                    obj = W_Object()
                    obj.Put(ctx, self.catchparam, e.exception)
                    ctx.push_object(obj)
                    try:
                        self.catchfunc.run(ctx)
                    finally:
                        ctx.pop_object()
                if self.finallyfunc is not None:
                    self.finallyfunc.run(ctx)
                if not self.catchfunc:
                    raise
        except ReturnException:
            # we run finally block here and re-raise the exception
            if self.finallyfunc is not None:
                self.finallyfunc.run(ctx)
            raise

    def __repr__(self):
        return "TRYCATCHBLOCK" # XXX shall we add stuff here???

class NEW(Opcode):
    def eval(self, ctx, stack):
        y = stack.pop()
        x = stack.pop()
        assert isinstance(y, W_List)
        args = y.get_args()
        stack.append(commonnew(ctx, x, args))

class NEW_NO_ARGS(Opcode):
    def eval(self, ctx, stack):
        x = stack.pop()
        stack.append(commonnew(ctx, x, []))

# ------------ iterator support ----------------

class LOAD_ITERATOR(Opcode):
    def eval(self, ctx, stack):
        obj = stack.pop().ToObject(ctx)
        props = [prop.value for prop in obj.propdict.values() if not prop.flags & jsobj.DE]
        stack.append(W_Iterator(props))

class JUMP_IF_ITERATOR_EMPTY(BaseJump):
    def eval(self, ctx, stack):
        pass

    def do_jump(self, stack, pos):
        iterator = stack.top()
        assert isinstance(iterator, W_Iterator)
        if iterator.empty():
            return self.where
        return pos + 1

class NEXT_ITERATOR(Opcode):
    def __init__(self, name):
        self.name = name

    def eval(self, ctx, stack):
        iterator = stack.top()
        assert isinstance(iterator, W_Iterator)
        ctx.assign(self.name, iterator.next())

# ---------------- with support ---------------------

class WITH_START(Opcode):
    def eval(self, ctx, stack):
        obj = stack.pop().ToObject(ctx)
        ctx.push_object(obj)

class WITH_END(Opcode):
    def eval(self, ctx, stack):
        ctx.pop_object()

# ------------------ delete -------------------------

class DELETE(Opcode):
    def __init__(self, name):
        self.name = name

    def eval(self, ctx, stack):
        stack.append(newbool(ctx.delete_identifier(self.name)))

class DELETE_MEMBER(Opcode):
    def eval(self, ctx, stack):
        what = stack.pop().ToString(ctx)
        obj = stack.pop().ToObject(ctx)
        stack.append(newbool(obj.Delete(what)))

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
