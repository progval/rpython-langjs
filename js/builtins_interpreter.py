from js.object_space import w_return, hide_on_translate
#from pypy.rlib import jit


def setup_builtins(global_object):
    from js.builtins import put_native_function

    put_native_function(global_object, u'load', js_load)
    put_native_function(global_object, u'debug', js_debug)
    put_native_function(global_object, u'trace', js_trace)


@w_return
def js_load(this, args):
    from js.object_space import object_space
    from js.interpreter import load_file
    filename = args[0].to_string()
    src = load_file(str(filename))
    object_space.interpreter.run_src(src)


@w_return
@hide_on_translate
def js_trace(this, args):
    import pdb
    pdb.set_trace()


@w_return
def js_debug(this, args):
    from js.object_space import object_space
    config = object_space.interpreter.config
    config.debug = not config.debug
    return config.debug
