class ObjectSpace(object):
    def __init__(self):
        self.global_object = None
        self.global_context = None

    def set_global_object(self, obj):
        self.global_object = obj

    def get_global_object(self):
        return self.global_object

    def set_global_context(self, ctx):
        self.global_context = ctx

    def get_global_context(self):
        return self.global_context

    def get_global_environment(self):
        return self.get_global_context().variable_environment()

object_space = ObjectSpace()
