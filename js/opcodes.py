from js.jsobj import W_IntNumber, W_FloatNumber, W_String,\
     W_Array, W_PrimitiveObject, ActivationObject,\
     create_object, W_Object, w_Undefined, newbool,\
     w_True, w_False, W_List, w_Null, W_Iterator, W_Root
import js.jsobj as jsobj
from js.execution import JsTypeError, ReturnException, ThrowException
from js.baseop import plus, sub, compare, AbstractEC, StrictEC,\
     compare_e, increment, decrement, commonnew, mult, division, uminus, mod
from pypy.rlib.rarithmetic import intmask

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

    def __repr__(self):
        return self.__class__.__name__

class BaseBinaryComparison(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        s4 = ctx.pop()
        s2 = ctx.pop()
        ctx.append(self.decision(ctx, s2, s4))

    def decision(self, ctx, op1, op2):
        raise NotImplementedError

class BaseBinaryBitwiseOp(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        s5 = ctx.pop().ToInt32(ctx)
        s6 = ctx.pop().ToInt32(ctx)
        ctx.append(self.operation(ctx, s5, s6))

    def operation(self, ctx, op1, op2):
        raise NotImplementedError

class BaseBinaryOperation(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        right = ctx.pop()
        left = ctx.pop()
        ctx.append(self.operation(ctx, left, right))

class BaseUnaryOperation(Opcode):
    _stack_change = 0

class Undefined(Opcode):
    def eval(self, ctx):
        ctx.append(w_Undefined)

class LOAD_INTCONSTANT(Opcode):
    _immutable_fields_ = ['w_intvalue']
    def __init__(self, value):
        self.w_intvalue = W_IntNumber(int(value))

    def eval(self, ctx):
        ctx.append(self.w_intvalue)

    def __repr__(self):
        return 'LOAD_INTCONSTANT %s' % (self.w_intvalue.intval,)

class LOAD_BOOLCONSTANT(Opcode):
    def __init__(self, value):
        self.boolval = value

    def eval(self, ctx):
        ctx.append(newbool(self.boolval))

class LOAD_FLOATCONSTANT(Opcode):
    def __init__(self, value):
        self.w_floatvalue = W_FloatNumber(float(value))

    def eval(self, ctx):
        ctx.append(self.w_floatvalue)

    def __repr__(self):
        return 'LOAD_FLOATCONSTANT %s' % (self.w_floatvalue.floatval,)

class LOAD_STRINGCONSTANT(Opcode):
    _immutable_fields_ = ['w_stringvalue']
    def __init__(self, value):
        self.w_stringvalue = W_String(value)

    def eval(self, ctx):
        ctx.append(self.w_stringvalue)

    #def get_literal(self, ctx):
    #    return W_String(self.strval).ToString(ctx)

    def __repr__(self):
        return 'LOAD_STRINGCONSTANT "%s"' % (self.w_stringvalue.strval,)

class LOAD_UNDEFINED(Opcode):
    def eval(self, ctx):
        ctx.append(w_Undefined)

class LOAD_NULL(Opcode):
    def eval(self, ctx):
        ctx.append(w_Null)

class LOAD_VARIABLE(Opcode):
    _immutable_fields_ = ['identifier']
    def __init__(self, identifier):
        self.identifier = identifier

    def eval(self, ctx):
        ctx.append(ctx.resolve_identifier(ctx, self.identifier))

    def __repr__(self):
        return 'LOAD_VARIABLE "%s"' % (self.identifier,)

class LOAD_REALVAR(Opcode):
    def __init__(self, depth, identifier):
        self.depth = depth
        self.identifier = identifier

    def eval(self, ctx):
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

    def eval(self, ctx):
        proto = ctx.get_global().Get(ctx, 'Array').Get(ctx, 'prototype')
        array = W_Array(ctx, Prototype=proto, Class = proto.Class)
        for i in range(self.counter):
            array.Put(ctx, str(self.counter - i - 1), ctx.pop())
        ctx.append(array)

    def stack_change(self):
        return -1 * self.counter + 1

    def __repr__(self):
        return 'LOAD_ARRAY %d' % (self.counter,)

class LOAD_LIST(Opcode):
    _immutable_fields_ = ['counter']
    def __init__(self, counter):
        self.counter = counter

    def eval(self, ctx):
        list_w = ctx.pop_n(self.counter)[:] # pop_n returns a non-resizable list
        ctx.append(W_List(list_w))

    def stack_change(self):
        return -1 * self.counter + 1

    def __repr__(self):
        return 'LOAD_LIST %d' % (self.counter,)

class LOAD_FUNCTION(Opcode):
    def __init__(self, funcobj):
        self.funcobj = funcobj

    def eval(self, ctx):
        proto = ctx.get_global().Get(ctx, 'Function').Get(ctx, 'prototype')
        w_func = W_Object(ctx=ctx, Prototype=proto, Class='Function',
                          callfunc=self.funcobj)
        w_func.Put(ctx, 'length', W_IntNumber(len(self.funcobj.params)))
        w_obj = create_object(ctx, 'Object')
        w_obj.Put(ctx, 'constructor', w_func, flags = jsobj.DONT_ENUM)
        w_func.Put(ctx, 'prototype', w_obj)
        ctx.append(w_func)

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

    def eval(self, ctx):
        w_obj = create_object(ctx, 'Object')
        for _ in range(self.counter):
            name = ctx.pop().ToString(ctx)
            w_elem = ctx.pop()
            w_obj.Put(ctx, name, w_elem)
        ctx.append(w_obj)

    def __repr__(self):
        return 'LOAD_OBJECT %d' % (self.counter,)

class LOAD_MEMBER(Opcode):
    _stack_change = -1
    def eval(self, ctx):
        w_obj = ctx.pop().ToObject(ctx)
        name = ctx.pop().ToString(ctx)
        ctx.append(w_obj.Get(ctx, name))

class COMMA(BaseUnaryOperation):
    def eval(self, ctx):
        one = ctx.pop()
        ctx.pop()
        ctx.append(one)
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
    def eval(self, ctx):
        one = ctx.pop()
        ctx.append(W_String(one.type()))

class TYPEOF_VARIABLE(Opcode):
    def __init__(self, name):
        self.name = name

    def eval(self, ctx):
        try:
            var = ctx.resolve_identifier(ctx, self.name)
            ctx.append(W_String(var.type()))
        except ThrowException:
            ctx.append(W_String('undefined'))

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
        op = ctx.pop().ToInt32(ctx)
        ctx.append(W_IntNumber(~op))

class URSH(BaseBinaryBitwiseOp):
    def eval(self, ctx):
        op2 = ctx.pop().ToUInt32(ctx)
        op1 = ctx.pop().ToUInt32(ctx)
        # XXX check if it could fit into int
        ctx.append(W_FloatNumber(op1 >> (op2 & 0x1F)))

class RSH(BaseBinaryBitwiseOp):
    def eval(self, ctx):
        op2 = ctx.pop().ToUInt32(ctx)
        op1 = ctx.pop().ToInt32(ctx)
        ctx.append(W_IntNumber(op1 >> intmask(op2 & 0x1F)))

class LSH(BaseBinaryBitwiseOp):
    def eval(self, ctx):
        op2 = ctx.pop().ToUInt32(ctx)
        op1 = ctx.pop().ToInt32(ctx)
        ctx.append(W_IntNumber(op1 << intmask(op2 & 0x1F)))

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
        if isinstance(ctx.top(), W_IntNumber):
            return
        if isinstance(ctx.top(), W_FloatNumber):
            return
        ctx.append(W_FloatNumber(ctx.pop().ToNumber(ctx)))

class UMINUS(BaseUnaryOperation):
    def eval(self, ctx):
        ctx.append(uminus(ctx.pop(), ctx))

class NOT(BaseUnaryOperation):
    def eval(self, ctx):
        ctx.append(newbool(not ctx.pop().ToBoolean()))

class INCR(BaseUnaryOperation):
    def eval(self, ctx):
        value = ctx.pop()
        newvalue = increment(ctx, value)
        ctx.append(newvalue)

class DECR(BaseUnaryOperation):
    def eval(self, ctx):
        value = ctx.pop()
        newvalue = decrement(ctx, value)
        ctx.append(newvalue)

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
        left = ctx.pop()
        member = ctx.pop()
        value = ctx.pop()
        name = member.ToString(ctx)
        left.ToObject(ctx).Put(ctx, name, value)
        ctx.append(value)

class STORE(Opcode):
    _immutable_fields_ = ['name']
    _stack_change = 0
    def __init__(self, name):
        self.name = name

    def eval(self, ctx):
        value = ctx.top()
        ctx.assign(self.name, value)

    def __repr__(self):
        return '%s "%s"' % (self.__class__.__name__, self.name)

class LABEL(Opcode):
    _stack_change = 0
    def __init__(self, num):
        self.num = num

    def __repr__(self):
        return 'LABEL %d' % (self.num,)

class BaseJump(Opcode):
    _immutable_fields_ = ['where']
    _stack_change = 0
    def __init__(self, where):
        self.where = where
        self.decision = False

    def do_jump(self, ctx, pos):
        return 0

    def __repr__(self):
        return '%s %d' % (self.__class__.__name__, self.where)

class JUMP(BaseJump):
    def eval(self, ctx):
        pass

    def do_jump(self, ctx, pos):
        return self.where

class BaseIfJump(BaseJump):
    def eval(self, ctx):
        value = ctx.pop()
        self.decision = value.ToBoolean()

class BaseIfNopopJump(BaseJump):
    def eval(self, ctx):
        value = ctx.top()
        self.decision = value.ToBoolean()

class JUMP_IF_FALSE(BaseIfJump):
    def do_jump(self, ctx, pos):
        if self.decision:
            return pos + 1
        return self.where

class JUMP_IF_FALSE_NOPOP(BaseIfNopopJump):
    def do_jump(self, ctx, pos):
        if self.decision:
            ctx.pop()
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
        ctx.pop()
        return pos + 1

class DECLARE_FUNCTION(Opcode):
    _stack_change = 0
    def __init__(self, funcobj):
        self.funcobj = funcobj

    def eval(self, ctx):
        # function declaration actyally don't run anything
        proto = ctx.get_global().Get(ctx, 'Function').Get(ctx, 'prototype')
        w_func = W_Object(ctx=ctx, Prototype=proto, Class='Function', callfunc=self.funcobj)
        w_func.Put(ctx, 'length', W_IntNumber(len(self.funcobj.params)))
        w_obj = create_object(ctx, 'Object')
        w_obj.Put(ctx, 'constructor', w_func, flags = jsobj.DONT_ENUM)
        w_func.Put(ctx, 'prototype', w_obj)
        if self.funcobj.name is not None:
            ctx.put(self.funcobj.name, w_func)

    def __repr__(self):
        funcobj = self.funcobj
        if funcobj.name is None:
            name = ""
        else:
            name = funcobj.name + " "
        codestr = '\n'.join(['  %r' % (op,) for op in funcobj.opcodes])
        return 'DECLARE_FUNCTION %s%r [\n%s\n]' % (name, funcobj.params, codestr)

class DECLARE_VAR(Opcode):
    _stack_change = 0
    def __init__(self, name):
        self.name = name

    def eval(self, ctx):
        ctx.declare_variable(self.name)

    def __repr__(self):
        return 'DECLARE_VAR "%s"' % (self.name,)

class RETURN(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        raise ReturnException(ctx.pop())

class POP(Opcode):
    _stack_change = -1
    def eval(self, ctx):
        ctx.pop()

def common_call(ctx, r1, args, this, name):
    if not isinstance(r1, W_PrimitiveObject):
        raise ThrowException(W_String("%s is not a callable (%s)"%(r1.ToString(ctx), name)))
    try:
        res = r1.Call(ctx=ctx, args=args.tolist(), this=this)
    except JsTypeError:
        raise ThrowException(W_String("%s is not a function (%s)"%(r1.ToString(ctx), name)))
    return res

class CALL(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        r1 = ctx.pop()
        args = ctx.pop()
        name = r1.ToString(ctx)
        this = ctx.to_context_object()
        #XXX hack, this should be comming from context
        ctx.append(common_call(ctx, r1, args, this, name))

class CALL_METHOD(Opcode):
    _stack_change = -2
    def eval(self, ctx):
        method = ctx.pop()
        what = ctx.pop().ToObject(ctx)
        args = ctx.pop()
        name = method.ToString(ctx)
        r1 = what.Get(ctx, name)
        ctx.append(common_call(ctx, r1, args, what, name))

class DUP(Opcode):
    def eval(self, ctx):
        ctx.append(ctx.top())

class THROW(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        val = ctx.pop()
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

    def __repr__(self):
        return "TRYCATCHBLOCK" # XXX shall we add stuff here???

class NEW(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        y = ctx.pop()
        x = ctx.pop()
        assert isinstance(y, W_List)
        args = y.get_args()
        ctx.append(commonnew(ctx, x, args))

class NEW_NO_ARGS(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        x = ctx.pop()
        ctx.append(commonnew(ctx, x, []))

# ------------ iterator support ----------------

class LOAD_ITERATOR(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        obj = ctx.pop().ToObject(ctx)
        props = [prop.value for prop in obj.propdict.values() if not prop.flags & jsobj.DONT_ENUM]
        ctx.append(W_Iterator(props))

class JUMP_IF_ITERATOR_EMPTY(BaseJump):
    def eval(self, ctx):
        pass

    def do_jump(self, ctx, pos):
        iterator = ctx.top()
        assert isinstance(iterator, W_Iterator)
        if iterator.empty():
            return self.where
        return pos + 1

class NEXT_ITERATOR(Opcode):
    _stack_change = 0
    def __init__(self, name):
        self.name = name

    def eval(self, ctx):
        iterator = ctx.top()
        assert isinstance(iterator, W_Iterator)
        ctx.assign(self.name, iterator.next())

# ---------------- with support ---------------------

class WITH_START(Opcode):
    _stack_change = 0
    def __init__(self):
        self.newctx = None

    def eval(self, ctx):
        obj = ctx.pop().ToObject(ctx)
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
        ctx.append(newbool(ctx.delete_identifier(self.name)))

class DELETE_MEMBER(Opcode):
    _stack_change = 0
    def eval(self, ctx):
        what = ctx.pop().ToString(ctx)
        obj = ctx.pop().ToObject(ctx)
        ctx.append(newbool(obj.Delete(what)))

class LOAD_LOCAL(Opcode):
    _immutable_fields_ = ['local']
    def __init__(self, local):
        self.local = local

    def eval(self, ctx):
        ctx.append(ctx.get_local_value(self.local))

    def __repr__(self):
        return 'LOAD_LOCAL %d' % (self.local,)

class STORE_LOCAL(Opcode):
    _stack_change = 0
    _immutable_fields_ = ['local']
    def __init__(self, local):
        self.local = local

    def eval(self, ctx):
        value = ctx.top()
        ctx.assign_local(self.local, value)

    def __repr__(self):
        return 'STORE_LOCAL %d' % (self.local,)

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
