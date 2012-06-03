# 8.9
class Completion(object):
    def __init__(self, value = None, target = None):
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
