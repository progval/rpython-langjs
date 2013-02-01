

# 8.9
class Completion(object):
    _immutable_fields_ = ['value', 'target']

    def __init__(self, value=None, target=None):
        self.value = value
        self.target = target


class NormalCompletion(Completion):
    pass


class ReturnCompletion(Completion):
    pass


class BreakCompletion(Completion):
    pass


class ContinueCompletion(Completion):
    pass


class ThrowCompletion(Completion):
    pass


def is_return_completion(c):
    return isinstance(c, ReturnCompletion)


def is_normal_completion(c):
    return isinstance(c, NormalCompletion)


def is_empty_completion(c):
    return is_normal_completion(c) and c.value is None


def is_completion(c):
    return isinstance(c, Completion)
