def to_string(this, *args):
    return "[object %s]" % (this.Class(), )

def value_of(this, *args):
    return this
