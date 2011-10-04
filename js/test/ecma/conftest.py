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
from js.interpreter import Interpreter, load_file, W_Builtin, W_IntNumber, W_Eval
from js.jsobj import W_Array, W_String
from js import interpreter
from js.execution import JsBaseExcept
from pypy.rlib.parsing.parsing import ParseError

interpreter.TEST = True

rootdir = py.path.local(__file__).dirpath()

def overriden_evaljs(ctx, args, this):
    try:
        w_eval = W_Eval(ctx)
        return w_eval.Call(ctx, args, this)
    except JsBaseExcept:
        return W_String("error")


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
        testcases = ctx.resolve_identifier(ctx, 'testcases')
        self.tc = ctx.resolve_identifier(ctx, 'tc')
        testcount = testcases.Get(ctx, 'length').ToInt32(ctx)
        self.testcases = testcases

        for number in xrange(testcount):
            yield JSTestItem(str(number), parent=self)

    def init_interp(cls):
        if hasattr(cls, 'interp'):
            cls.testcases.PutValue(W_Array(), cls.interp.global_context)
            cls.tc.PutValue(W_IntNumber(0), cls.interp.global_context)

        cls.interp = Interpreter()
        shellpath = rootdir/'shell.js'
        if not hasattr(cls, 'shellfile'):
            cls.shellfile = load_file(str(shellpath))
        cls.interp.run(cls.shellfile)
        cls.testcases = cls.interp.global_context.resolve_identifier(cls.interp.global_context, 'testcases')
        cls.tc = cls.interp.global_context.resolve_identifier(cls.interp.global_context, 'tc')
        # override eval
        cls.interp.w_Global.Put(cls.interp.global_context, 'eval', W_Builtin(overriden_evaljs))

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
        r3 = ctx.resolve_identifier(ctx, 'run_test')
        w_test_number = W_IntNumber(self.test_number)
        result = r3.Call(ctx=ctx, args=[w_test_number]).ToString()
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

