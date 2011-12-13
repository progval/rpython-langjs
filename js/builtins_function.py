def to_string(this, *args):
    return this.ToString()

def empty(this, *args):
    from js.jsobj import w_Undefined
    return w_Undefined
