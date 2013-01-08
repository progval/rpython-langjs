from js.object_space import _w


def to_string(this, args):
    s = "[object %s]" % (this.klass(), )
    return _w(s)


def value_of(this, args):
    return this
