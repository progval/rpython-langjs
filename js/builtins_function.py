from js.jsobj import isnull_or_undefined
from js.execution import JsTypeError
from js.jsobj import w_Undefined, _w, isnull_or_undefined
from js.builtins import get_arg
from js.completion import NormalCompletion

def to_string(this, args):
    from js.jsobj import W_BasicFunction
    if not isinstance(this, W_BasicFunction):
        raise JsTypeError(u'')

    return _w(this._to_string_())

def empty(this, args):
    return w_Undefined

# 15.3.4.4 Function.prototype.call
def js_call(ctx):
    func = ctx.this_binding()
    args = ctx.argv()

    if not func.is_callable():
        raise JsTypeError(u'')

    this_arg = get_arg(args, 0)
    arg_list = args[1:]

    res = func.Call(args = arg_list, this = this_arg, calling_context = ctx)
    compl = NormalCompletion(value = _w(res))
    return compl

# 15.3.4.3 Function.prototype.apply (thisArg, argArray)
def js_apply(ctx):
    func = ctx.this_binding()
    args = ctx.argv()

    this_arg = get_arg(args, 0)
    arg_array = get_arg(args, 1)

    if isnull_or_undefined(arg_array):
        res = func.Call(args = [], this = this_arg, calling_context = ctx)
        compl = NormalCompletion(value = _w(res))
        return compl

    from js.jsobj import W_BasicObject
    if not isinstance(arg_array, W_BasicObject):
        raise JsTypeError(u'')

    length = arg_array.get(u'length')
    n = length.ToUInt32()
    arg_list = []
    index = 0
    while index < n:
        index_name = unicode(str(index))
        next_arg = arg_array.get(index_name)
        arg_list.append(next_arg)
        index += 1

    res = func.Call(args = arg_list, this = this_arg, calling_context = ctx)
    compl = NormalCompletion(value = _w(res))
    return compl
