# encoding: utf-8
from js.jsobj import W_Root
from pypy.rlib.jit import hint
from pypy.rlib import jit, debug

class Stack(object):
    _virtualizable2_ = ['content[*]', 'pointer']
    def __init__(self, size):
        self = hint(self, access_directly = True, fresh_virtualizable = True)
        self.content = [None] * size
        self.pointer = 0

    def __repr__(self):
        return "<Stack %(content)s@%(pointer)d>" % {'pointer': self.pointer, 'content': self.content}

    def pop(self):
        e = self.top()
        i = self.pointer - 1
        assert i >= 0
        self.content[i] = None
        self.pointer = i
        return e

    def top(self):
        i = self.pointer - 1
        if i < 0:
            raise IndexError
        return self.content[i]

    def append(self, element):
        assert isinstance(element, W_Root)
        i = self.pointer
        assert i >= 0
        self.content[i] = element
        self.pointer = i + 1

    @jit.unroll_safe
    def pop_n(self, n):
        l = [None] * n
        for i in range(n-1, -1, -1):
            l[i] = self.pop()
        debug.make_sure_not_resized(l)
        return l

    def check(self):
        assert self.pointer == 1
