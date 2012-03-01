from js.jsobj import isnull_or_undefined

def to_string(this, args):
    return this.ToString()

def empty(this, args):
    from js.jsobj import w_Undefined
    return w_Undefined

# 15.3.4.4 Function.prototype.call
def call(this, args):
    pass
    #if len(args) >= 1:
        #if isnull_or_undefined(args[0]):
            #thisArg = this.ctx.get_global()
        #else:
            #thisArg = args[0]
        #callargs = args[1:]
    #else:
        #thisArg = this.ctx.get_global()
        #callargs = []
    #return this.Call(callargs, this = thisArg)

# 15.3.4.3 Function.prototype.apply (thisArg, argArray)
def apply(this, args):
    pass
    #try:
        #if isnull_or_undefined(args[0]):
            #thisArg = this.ctx.get_global()
        #else:
            #thisArg = args[0].ToObject()
    #except IndexError:
        #thisArg = this.ctx.get_global()

    #try:
        #arrayArgs = args[1]
        #callargs = arrayArgs.tolist()
    #except IndexError:
        #callargs = []
    #return this.Call(callargs, this=thisArg)
