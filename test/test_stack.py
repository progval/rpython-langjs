import py

from js.utils import StackMixin

class Stack(StackMixin):
    def __init__(self, size, resize = True):
        self._init_stack_(size, resize)

    def pop(self):
        return self._stack_pop()

    def append(self, value):
        self._stack_append(value)

    def top(self):
        return self._stack_top()

    def pop_n(self, n):
        return self._stack_pop_n(n)

class TestStack(object):
    def test_stack_push(self):
        s = Stack(99)
        assert len(s._stack_) == 99
        assert s._stack_ == [None] * 99

        s = Stack(99)
        s.append(1)
        assert s._stack_[0] == 1
        assert s._stack_pointer_ == 1

        s = Stack(99)
        s.append(1)
        s.append(2)
        s.append(3)
        assert s._stack_[0] == 1
        assert s._stack_[1] == 2
        assert s._stack_[2] == 3
        assert s._stack_pointer_ == 3

    def test_stack_pop(self):
        s = Stack(99)
        s.append(1)
        s.append(2)
        s.append(3)
        assert s.pop() == 3
        assert s._stack_pointer_ == 2
        assert s._stack_[2] == None

        s = Stack(99)
        s.append(1)
        s.append(2)
        s.append(3)
        assert s.pop() == 3
        assert s.pop() == 2
        assert s.pop() == 1

    def test_stack_last(self):
        s = Stack(99)
        s.append(1)
        assert s.top() == 1

        s = Stack(99)
        s.append(1)
        s.append(2)
        s.append(3)
        assert s.top() == 3

    def test_stack_popn(self):
        s = Stack(99)
        s.append(1)
        s.append(2)
        s.append(3)
        x = s.pop_n(2)
        assert x == [2, 3]
        assert s._stack_pointer_ == 1
        assert s._stack_[1] == None
        assert s._stack_[2] == None

    def test_stack_no_resize(self):
        s = Stack(2, False)
        s.append(1)
        s.append(1)
        py.test.raises(AssertionError, s.append,1)

    def test_stack_resize(self):
        s = Stack(0)
        s.append(1)
        s.append(2)
        s.append(3)
        assert len(s._stack_) == 3
