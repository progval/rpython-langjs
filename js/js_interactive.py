#!/usr/bin/env python
# encoding: utf-8
"""
js_interactive.py
"""

import sys
import getopt
from js.interpreter import Interpreter, load_file
from js.jsparser import parse, ParseError
from js.jsobj import W_String, w_Undefined, W_Boolean
from pypy.rlib.streamio import open_file_as_stream

#sys.setrecursionlimit(100)

import code
sys.ps1 = 'js> '
sys.ps2 = '... '

try:
    # Setup Readline
    import readline
    import os
    histfile = os.path.join(os.environ["HOME"], ".jspypyhist")
    try:
        getattr(readline, "clear_history", lambda : None)()
        readline.read_history_file(histfile)
    except IOError:
        pass
    import atexit
    atexit.register(readline.write_history_file, histfile)
except ImportError:
    pass

DEBUG = False

def debugjs(this, args):
    global DEBUG
    DEBUG = not DEBUG
    return W_Boolean(DEBUG)

def tracejs(this, args):
    arguments = args
    import pdb
    pdb.set_trace()
    return w_Undefined

def quitjs(this, args):
    sys.exit(0)

class JSInterpreter(code.InteractiveConsole):
    def __init__(self, locals=None, filename="<console>"):
        code.InteractiveConsole.__init__(self, locals, filename)
        self.interpreter = Interpreter()
        #ctx = self.interpreter.global_context
        #from builtins import new_native_function
        #self.interpreter.w_Global.Put('quit', new_native_function(ctx, quitjs))
        #self.interpreter.w_Global.Put('trace', new_native_function(ctx, tracejs))
        #self.interpreter.w_Global.Put('debug', new_native_function(ctx, debugjs))

    def runcodefromfile(self, filename):
        f = open_file_as_stream(filename)
        self.runsource(f.readall(), filename)
        f.close()

    def runcode(self, ast):
        """Run the javascript code in the AST. All exceptions raised
        by javascript code must be caught and handled here. When an
        exception occurs, self.showtraceback() is called to display a
        traceback.
        """
        from js.execution import JsException
        try:
            res = self.interpreter.run_ast(ast)
            try:
                print res.to_string()
            except JsException, exc:
                self.showtraceback(exc)
        except SystemExit:
            raise
        except JsException, exc:
            self.showtraceback(exc)
        else:
            if code.softspace(sys.stdout, 0):
                print

    def runsource(self, source, filename="<input>"):
        from js.astbuilder import parse_to_ast
        """Parse and run source in the interpreter.

        One of these cases can happen:
        1) The input is incorrect. Prints a nice syntax error message.
        2) The input in incomplete. More input is required. Returns None.
        3) The input is complete. Executes the source code.
        """
        try:
            ast = parse_to_ast(str(source))
        except ParseError, exc:
            if exc.source_pos.i == len(source):
                # Case 2
                return True # True means that more input is needed
            else:
                # Case 1
                self.showsyntaxerror(filename, exc, source)
                return False

        # Case 3
        self.runcode(ast)
        return False

    def showtraceback(self, exc):
        # XXX format exceptions nicier
        print exc.value.to_string()

    def showsyntaxerror(self, filename, exc, source):
        # XXX format syntax errors nicier
        marker_indent = ' ' * exc.source_pos.columnno
        error = exc.errorinformation.failure_reasons
        error_lineno = exc.source_pos.lineno
        error_line = (source.splitlines())[error_lineno]
        print 'Syntax Error in: %s:%d' % (filename, error_lineno)
        print '%s' % (error_line)
        print '%s^' %(marker_indent)
        print 'Error: %s' %(error)

    def interact(self, banner=None):
        if banner is None:
            banner = 'PyPy JavaScript Interpreter'
        code.InteractiveConsole.interact(self, banner)

def main(inspect=False, files=[]):
    jsi = JSInterpreter()
    for filename in files:
        jsi.runcodefromfile(filename)
    if (not files) or inspect:
        jsi.interact()

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser(usage='%prog [options] [files] ...',
                          description='PyPy JavaScript Interpreter')
    parser.add_option('-i', dest='inspect',
                    action='store_true', default=False,
                    help='inspect interactively after running script')

    # ... (add other options)
    opts, args = parser.parse_args()

    if args:
        main(inspect=opts.inspect, files=args)
    else:
        main(inspect=opts.inspect)
    sys.exit(0)
