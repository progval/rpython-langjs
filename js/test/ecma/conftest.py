import pytest
import py

from _pytest.runner import Failed
from js.interpreter import Interpreter, load_file
from js.jsobj import _w
from js import interpreter
from js.execution import JsException
from pypy.rlib.parsing.parsing import ParseError


exclusionlist = ['shell.js', 'browser.js']
skip = [\
    '15.4.5.1-1',
    '10.2.2-2',
    '15.1.2.1-2',
    '15.5.4.11-2',
    '15.5.4.11-5',
    '7.2-1',
    '7.4.3-14-n',
    '7.4.3-15-n',
    '7.4.3-4-n',
    '7.4.3-7-n',
    '7.4.3-9-n',
    '7.7.3-2',
    '7.7.4',
    '11.2.1-3-n',
    '12.10-1',
    '12.7-1-n',
    '12.8-1-n',
    ]

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

rootdir = py.path.local(__file__).dirpath()

class JSTestFile(pytest.File):
    def __init__(self, fspath, parent=None, config=None, session=None):
        super(JSTestFile, self).__init__(fspath, parent, config, session)
        self.name = self.fspath.purebasename


    def collect(self):
        if self.session.config.getvalue("ecma") is not True:
            pytest.skip("ECMA tests disabled, run with --ecma")
        if self.name in skip:
            pytest.skip()

        interp = Interpreter()

        # the tests expect eval to return "error" on an exception
        from js.builtins import put_intimate_function
        def overriden_eval(ctx):
            from js.builtins_global import js_eval
            from js.execution import JsException
            try:
                return js_eval(ctx)
            except JsException:
                return _w("error")

        global_object = interp.global_object
        del(global_object._properties_['eval'])
        put_intimate_function(global_object, 'eval', overriden_eval, configurable = False, params = ['x'])

        shellpath = rootdir/'shell.js'
        shellfile = load_file(str(shellpath))
        interp.run_ast(shellfile)

        #actually run the file :)
        t = load_file(str(self.fspath))
        try:
            interp.run_ast(t)
        except ParseError, e:
            raise Failed(msg=e.nice_error_message(filename=str(self.fspath))) #, excinfo=None)
        #except JsException, e:
            #import pdb; pdb.set_trace()
            #raise Failed(msg="Javascript Error: "+str(e)) #, excinfo=py.code.ExceptionInfo())

        testcases = global_object.get('testcases')
        #tc = global_object.get('tc')
        #self.tc = tc
        testcount = testcases.get('length').ToInt32()
        self.testcases = testcases

        run_test_func = global_object.get('run_test')
        def get_result(test_num):
            w_test_number = _w(test_num)
            result = run_test_func.Call(args = [w_test_number])
            return result.to_string()

        for number in xrange(testcount):
            result = get_result(number)
            yield JSTestItem(str(number), result, parent=self)

class JSTestItem(pytest.Item):
    def __init__(self, name, result, parent=None, config=None, session=None):
        super(JSTestItem, self).__init__(name, parent, config, session)
        self.test_number = int(name)
        self.name = parent.name + '.' + name
        self.result = result

    def runtest(self):
        result = self.result
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

class JsTestException(Exception):
    def __init__(self, item, result):
        self.item = item
        self.result = result

