#!/usr/bin/env python

import os, sys
from js.execution import JsException
from pypy.rlib.objectmodel import enforceargs
from pypy.rlib.parsing.parsing import ParseError

def main(argv):
    opts, files = parse_args(argv)

    debug = opts.get('debug', False)
    inspect = opts.get('inspect', False)

    try:
        run(files, debug, inspect)
    except SystemExit:
        printmessage(u"\n")

    return 0

def run(files, debug, inspect):
    from js.object_space import object_space
    from js.interpreter import Interpreter

    interactive = len(files) == 0

    object_space.DEBUG = debug
    interp = Interpreter()

    for f in files:
        try:
            interp.run_file(f)
        except JsException as e:
            printerrormessage(unicode(f), e._msg())
            raise SystemExit

    if inspect or interactive:
        repl(interp)

@enforceargs(unicode, unicode)
def printerrormessage(filename, message):
    printmessage(u"ERROR in %s: %s\n" % (filename, message))


def repl(interpreter):
    filename = u'<stdin>'
    while True:
        printmessage(u'js> ')
        line = readline()

        try:
            result = interpreter.run_src(line)
            result_string = result.to_string()
            printmessage(u"%s\n"% (result_string))
        except ParseError as exc:
            printsyntaxerror(filename, exc, line)
            continue
        except JsException as e:
            printerrormessage(filename, e._msg())
            continue

# https://bitbucket.org/cfbolz/pyrolog/src/f18f2ccc23a4/prolog/interpreter/translatedmain.py
@enforceargs(unicode)
def printmessage(msg):
    from js.runistr import encode_unicode_utf8
    os.write(1, encode_unicode_utf8(msg))

def printsyntaxerror(filename, exc, source):
    # XXX format syntax errors nicier
    marker_indent = u' ' * exc.source_pos.columnno
    error = exc.errorinformation.failure_reasons
    error_lineno = exc.source_pos.lineno
    error_line = (source.splitlines())[error_lineno]
    printmessage(u'Syntax Error in: %s:%d\n' % (unicode(filename), error_lineno))
    printmessage(u'%s\n' % (unicode(error_line)))
    printmessage(u'%s^\n' %(marker_indent))
    printmessage(u'Error: %s\n' %(unicode(str(error))))

# https://bitbucket.org/cfbolz/pyrolog/src/f18f2ccc23a4/prolog/interpreter/translatedmain.py
def readline():
    result = []
    while True:
        s = os.read(0, 1)
        result.append(s)
        if s == "\n":
            break
        if s == '':
            if len(result) > 1:
                break
            raise SystemExit
    return "".join(result)

def parse_args(argv):
    opts = {'inspect': False, 'debug': False}

    for i in xrange(len(argv)):
        if argv[i] == '-d':
            opts['debug'] = True
            del(argv[i])
            break

    for i in xrange(len(argv)):
        if argv[i] == '-i':
            opts['inspect'] = True
            del(argv[i])
            break

    del(argv[0])

    return opts, argv

if __name__ == '__main__':
    import sys
    main(sys.argv)

# _____ Define and setup target ___

def target(driver, args):
    driver.exe_name = 'py-js'
    return entry_point, None

def jitpolicy(driver):
    from pypy.jit.codewriter.policy import JitPolicy
    return JitPolicy()

def entry_point(argv):
    return main(argv)
