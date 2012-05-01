import pytest

exclusionlist = ['shell.js', 'browser.js']
#passing_tests = ['Number', 'Boolean', 'Array']

def pytest_ignore_collect(path, config):
    if path.basename in exclusionlist:
        return True

def pytest_collect_file(path, parent):
    if path.ext == ".js":
        return JSTestFile(path, parent=parent)

def pytest_addoption(parser):
    parser.addoption('--ecma',
           action="store_true", dest="ecma", default=False,
           help="run js interpreter ecma tests"
    )

import py

from _pytest.runner import Failed
from js.interpreter import Interpreter, load_file
from js.jsobj import _w
from js import interpreter
from js.execution import JsBaseExcept
from pypy.rlib.parsing.parsing import ParseError

interpreter.TEST = True

rootdir = py.path.local(__file__).dirpath()


class JSTestFile(pytest.File):
    def __init__(self, fspath, parent=None, config=None, session=None):
        super(JSTestFile, self).__init__(fspath, parent, config, session)
        self.name = self.fspath.purebasename

    def collect(self):
        if self.session.config.getvalue("ecma") is not True:
            pytest.skip("ECMA tests disabled, run with --ecma")


        self.init_interp()
        #actually run the file :)
        t = load_file(str(self.fspath))
        try:
            self.interp.run(t)
        except ParseError, e:
            raise Failed(msg=e.nice_error_message(filename=str(self.fspath))) #, excinfo=None)
        except JsBaseExcept, e:
            raise Failed(msg="Javascript Error: "+str(e)) #, excinfo=py.code.ExceptionInfo())
        except:
            raise
        ctx = self.interp.global_context
        testcases = ctx.resolve_identifier('testcases')
        self.tc = ctx.resolve_identifier('tc')
        testcount = testcases.Get('length').ToInt32()
        self.testcases = testcases

        for number in xrange(testcount):
            yield JSTestItem(str(number), parent=self)

    def init_interp(cls):
        if hasattr(cls, 'interp'):
            from js.jsobj import W__Array
            cls.testcases.PutValue(W__Array(), cls.interp.global_context)
            cls.tc.PutValue(_w(0), cls.interp.global_context)

        cls.interp = Interpreter()
        shellpath = rootdir/'shell.js'
        if not hasattr(cls, 'shellfile'):
            cls.shellfile = load_file(str(shellpath))
        cls.interp.run(cls.shellfile)
        cls.testcases = cls.interp.global_context.resolve_identifier('testcases')
        cls.tc = cls.interp.global_context.resolve_identifier('tc')

        # override eval
        from js.builtins import new_native_function

        ctx = cls.interp.global_context
        def overriden_evaljs(this, args):
            from js.builtins import W__Eval
            try:
                w_eval = W__Eval(ctx)
                return w_eval.Call(args, this)
            except JsBaseExcept:
                return "error"

        cls.interp.w_Global.Put('eval', new_native_function(ctx, overriden_evaljs, 'eval'))

#
#    init_interp = classmethod(init_interp)
#
#
#

class JSTestItem(pytest.Item):
    def __init__(self, name, parent=None, config=None, session=None):
        super(JSTestItem, self).__init__(name, parent, config, session)
        self.test_number = int(name)
        self.name = parent.name + '.' + name

    def runtest(self):
        ctx = self.parent.interp.global_context
        r3 = ctx.resolve_identifier('run_test')
        w_test_number = _w(self.test_number)
        result = r3.Call([w_test_number]).ToString()
        __tracebackhide__ = True
        if result != "passed":
            raise JsTestException(self, result)

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, JsTestException):
            return "\n".join([
                "test execution failed",
                "   failed: %r:" % (excinfo.value.item.name),
                "   :%r" % (excinfo.value.result)
            ])

    _handling_traceback = False
#    def _getpathlineno(self):
#        return self.parent.parent.fspath, 0
#

class JsTestException(Exception):
    def __init__(self, item, result):
        self.item = item
        self.result = result

