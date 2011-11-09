# encoding: utf-8
from pypy.rlib.jit import hint
from pypy.rlib import jit, debug

class StackMixin(object):
    _mixin_ = True
    def __init__(self):
        self._init_stack()

    def _init_stack(self, size = 1):
        self.stack = [None] * size
        self.stack_pointer = 0

    def pop(self):
        e = self.top()
        i = self.stack_pointer - 1
        assert i >= 0
        self.stack[i] = None
        self.stack_pointer = i
        return e

    def top(self):
        i = self.stack_pointer - 1
        if i < 0:
            raise IndexError
        return self.stack[i]

    def append(self, element):
        from js.jsobj import W___Root
        assert isinstance(element, W___Root)
        i = self.stack_pointer
        assert i >= 0
        self.stack[i] = element
        self.stack_pointer = i + 1

    @jit.unroll_safe
    def pop_n(self, n):
        l = [None] * n
        for i in range(n-1, -1, -1):
            l[i] = self.pop()
        debug.make_sure_not_resized(l)
        return l

    def check_stack(self):
        assert self.stack_pointer == 1
