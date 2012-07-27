"""
A simple standalone target for the javascript interpreter.
"""

import sys
from js.interpreter import Interpreter
from js.execution import ExecutionReturned

# __________  Entry point  __________


def entry_point(argv):
    debug = False

    for i in xrange(len(argv)):
        if argv[i] == '-d':
            debug = True
            del(argv[i])
            break

    if len(argv) == 2:
        from js.object_space import object_space
        object_space.DEBUG = debug
        interp = Interpreter()
        interp.run_file(argv[1])
        return 0
    elif argv[0] == 'foo':
        raise ExecutionReturned(None)
    else:
        print "Usage: %s jsourcefile" % argv[0]
        return 1

# _____ Define and setup target ___

def target(driver, args):
    driver.exe_name = 'js-%(backend)s'
    return entry_point, None

def jitpolicy(driver):
    from pypy.jit.codewriter.policy import JitPolicy
    return JitPolicy()

if __name__ == '__main__':
    entry_point(sys.argv)
