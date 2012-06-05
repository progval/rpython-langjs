import pytest
import py

from _pytest.runner import Failed
from js.interpreter import Interpreter, load_file
from js.jsobj import _w
from js import interpreter
from js.execution import JsException
from pypy.rlib.parsing.parsing import ParseError


EXCLUSIONLIST = ['shell.js', 'browser.js']
SKIP = [\
    '7.2-1.0',
    '7.2-1.1',
    '7.2-1.2',
    '7.2-1.3',
    '7.2-1.4',
    '7.2-1.5',
    '7.4.3-14-n',
    '7.4.3-15-n',
    '7.4.3-4-n',
    '7.4.3-7-n',
    '7.4.3-9-n',
    '7.7.3-2',
    '7.7.4',
    '7.2-6.0',
    '7.2-6.1',
    '7.4.3-13-n.0',
    '7.4.3-2-n.0',
    '7.4.3-3-n.0',
    '7.6.14',
    '7.6.15',
    '7.7.3-1.9',
    '7.7.3-1.11',
    '7.7.3-1.12',
    '7.7.3-1.13',
    '7.7.3-1.15',
    '7.7.3-1.16',
    '7.7.3-1.17',
    '7.7.3-1.18',
    '7.7.3-1.20',
    '7.7.3-1.21',
    '7.7.3-1.22',
    '7.7.3-1.23',
    '7.7.3-1.25',
    '7.7.3.155',
    '7.7.3.156',
    '7.7.3.157',
    '7.7.3.161',
    '7.7.3.162',
    '7.7.3.163',
    '7.7.3.167',
    '9.8.1.12',
    '9.8.1.13',
    '9.8.1.22',
    '9.8.1.35',
    '9.4-1.0',
    '9.4-1.1',
    '9.4-1.2',
    '9.4-2.0',
    '9.4-2.1',
    '9.4-2.2',
    '9.8.1.36',
    '9.3.1-3.39',
    '9.3.1-3.41',
    '9.3.1-3.42',
    '9.3.1-3.43',
    '9.3.1-3.45',
    '9.3.1-3.46',
    '9.3.1-3.47',
    '9.3.1-3.48',
    '9.3.1-3.50',
    '9.3.1-3.51',
    '9.3.1-3.52',
    '9.3.1-3.53',
    '9.3.1-3.55',
    '9.3.1-3.104',
    '10.2.2-2.1',
    '11.2.1-3-n.0',
    '11.2.1-3-n.1',
    '12.10-1',
    '12.6.3-2.0',
    '12.7-1-n',
    '12.8-1-n',
    '12.9-1-n.0',
    '15.1.2.1-2.0',
    '15.4.4.5-3',
    '15.4.5.1-1',
    '15.5.4.11-2.0',
    '15.5.4.11-2.1',
    '15.5.4.11-2.2',
    '15.5.4.11-2.3',
    '15.5.4.11-2.4',
    '15.5.4.11-2.5',
    '15.5.4.11-2.6',
    '15.5.4.11-2.7',
    '15.5.4.11-2.8',
    '15.5.4.11-2.9',
    '15.5.4.11-2.10',
    '15.5.4.11-2.11',
    '15.5.4.11-2.12',
    '15.5.4.11-2.13',
    '15.5.4.11-2.14',
    '15.5.4.11-2.15',
    '15.5.4.11-2.16',
    '15.5.4.11-2.17',
    '15.5.4.11-2.18',
    '15.5.4.11-2.19',
    '15.5.4.11-2.20',
    '15.5.4.11-2.21',
    '15.5.4.11-2.22',
    '15.5.4.11-2.23',
    '15.5.4.11-2.24',
    '15.5.4.11-2.25',
    '15.5.4.11-2.26',
    '15.5.4.11-2.27',
    '15.5.4.11-2.28',
    '15.5.4.11-2.29',
    '15.5.4.11-2.30',
    '15.5.4.11-2.31',
    '15.5.4.11-2.32',
    '15.5.4.11-2.33',
    '15.5.4.11-2.34',
    '15.5.4.11-2.35',
    '15.5.4.11-2.36',
    '15.5.4.11-2.37',
    '15.5.4.11-5.3',
    '15.5.4.11-5.16',
    '15.5.1.22',
    '15.5.1.23',
    '15.5.1.32',
    '15.5.1.45',
    '15.5.1.46',
    '15.5.4.12-1.184',
    '15.5.4.12-4.80',
    '15.5.4.12-4.93',
    ]


def pytest_ignore_collect(path, config):
    if path.basename in EXCLUSIONLIST:
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
        if self.name in SKIP:
            pytest.skip()

        interp = Interpreter()

        # the tests expect eval to return "error" on an exception
        from js.builtins import put_intimate_function
        def overriden_eval(ctx):
            from js.builtins_global import js_eval
            from js.execution import JsException
            from js.completion import NormalCompletion
            try:
                return js_eval(ctx)
            except JsException:
                return NormalCompletion(value = _w("error"))

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
            result_obj = run_test_func.Call(args = [w_test_number])
            result_passed = result_obj.get('passed').ToBoolean()
            result_reason = result_obj.get('reason').to_string();
            return (result_passed, result_reason) # result.to_string()

        for number in xrange(testcount):
            passed, reason = get_result(number)
            yield JSTestItem(str(number), passed, reason, parent=self)

class JSTestItem(pytest.Item):
    def __init__(self, name, passed, reason, parent=None, config=None, session=None):
        super(JSTestItem, self).__init__(name, parent, config, session)
        self.test_number = int(name)
        self.name = parent.name + '.' + name
        self.passed = passed
        self.reason = reason

    def runtest(self):
        reason = self.reason
        passed = self.passed
        if self.name in SKIP:
            py.test.skip()
        __tracebackhide__ = True
        if passed != True:
            raise JsTestException(self, reason)

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

