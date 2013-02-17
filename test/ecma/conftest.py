import pytest
import py
from _pytest.runner import Failed
from rpython.rlib.parsing.parsing import ParseError

from js.interpreter import Interpreter, load_file
from js.object_space import _w
from js.exception import JsException

EXCLUSIONLIST = ['shell.js', 'browser.js']
SKIP = [
    '10.2.2-2.1',
    '11.2.1-1.250',
    '11.2.1-1.251',
    '11.2.1-3-n.0',
    '11.2.1-3-n.1',
    '12.10-1',
    '12.6.3-2.0',
    '12.7-1-n',
    '12.8-1-n',
    '12.9-1-n.0',
    '15.1.2.1-2.0',
    '15.1.2.2-2.1',
    '15.1.2.2-2.13',
    '15.1.2.2-2.2',
    '15.1.2.2-2.21',
    '15.1.2.2-2.22',
    '15.1.2.2-2.3',
    '15.1.2.2-2.4',
    '15.1.2.2-2.6',
    '15.4.4.3-1.9',
    '15.4.4.5-3',
    '15.4.5.1-1',
    '15.5.1.22',
    '15.5.1.23',
    '15.5.1.32',
    '15.5.1.45',
    '15.5.1.46',
    '15.5.4.10-1',
    '15.5.4.11-2.0',
    '15.5.4.11-2.1',
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
    '15.5.4.11-2.2',
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
    '15.5.4.11-2.3',
    '15.5.4.11-2.30',
    '15.5.4.11-2.31',
    '15.5.4.11-2.32',
    '15.5.4.11-2.33',
    '15.5.4.11-2.34',
    '15.5.4.11-2.35',
    '15.5.4.11-2.36',
    '15.5.4.11-2.37',
    '15.5.4.11-2.4',
    '15.5.4.11-2.5',
    '15.5.4.11-2.6',
    '15.5.4.11-2.7',
    '15.5.4.11-2.8',
    '15.5.4.11-2.9',
    '15.5.4.11-5.16',
    '15.5.4.11-5.3',
    '15.5.4.12-1.184',
    '15.5.4.12-4.80',
    '15.5.4.12-4.93',
    '15.5.4.4-2',
    '15.5.4.5-2',
    '15.5.4.5-5',
    '15.5.4.6-2.231',
    '15.5.4.6-2.231',
    '15.5.4.9-1',
    '15.8.2.13.35',
    '15.8.2.13.57',
    '15.8.2.13.58',
    '7.2-1.0',
    '7.2-1.1',
    '7.2-1.2',
    '7.2-1.3',
    '7.2-1.4',
    '7.2-1.5',
    '7.2-6.0',
    '7.2-6.1',
    '7.4.3-13-n.0',
    '7.4.3-14-n',
    '7.4.3-15-n',
    '7.4.3-2-n.0',
    '7.4.3-3-n.0',
    '7.4.3-4-n',
    '7.4.3-7-n',
    '7.4.3-9-n',
    '7.6.14',
    '7.6.15',
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
    '7.7.3-1.9',
    '7.7.3-2',
    '7.7.3.155',
    '7.7.3.156',
    '7.7.3.157',
    '7.7.3.161',
    '7.7.3.162',
    '7.7.3.163',
    '7.7.3.167',
    '7.7.4',
    '9.3.1-3.104',
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
    '9.4-1.0',
    '9.4-1.1',
    '9.4-1.10',
    '9.4-1.11',
    '9.4-1.12',
    '9.4-1.13',
    '9.4-1.14',
    '9.4-1.15',
    '9.4-1.16',
    '9.4-1.17',
    '9.4-1.18',
    '9.4-1.2',
    '9.4-1.3',
    '9.4-1.4',
    '9.4-1.5',
    '9.4-1.6',
    '9.4-1.7',
    '9.4-1.8',
    '9.4-1.9',
    '9.4-2.0',
    '9.4-2.1',
    '9.4-2.10',
    '9.4-2.11',
    '9.4-2.12',
    '9.4-2.13',
    '9.4-2.14',
    '9.4-2.15',
    '9.4-2.16',
    '9.4-2.17',
    '9.4-2.18',
    '9.4-2.2',
    '9.4-2.3',
    '9.4-2.4',
    '9.4-2.5',
    '9.4-2.6',
    '9.4-2.7',
    '9.4-2.8',
    '9.4-2.9',
    '9.8.1.12',
    '9.8.1.13',
    '9.8.1.22',
    '9.8.1.35',
    '9.8.1.36',
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
                     help="run js interpreter ecma tests")
    parser.addoption('--ecma-compile',
                     action="store_true", dest="ecma-compile", default=False,
                     help="run js interpreter ecma tests")

rootdir = py.path.local(__file__).dirpath()
shellpath = rootdir / 'shell.js'
_compiled_f = None


class InterpreterResults(object):
    compiled_interpreter = None

    def __init__(self, do_compile):
        self.do_compile = do_compile

    def get_interp(self):
        def f(testfile):
            interp = Interpreter({'no-exception-jseval': True})

            shell_src = load_file(str(shellpath))
            interp.run_src(shell_src)
            test_src = load_file(testfile)
            interp.run_src(test_src)

            global_object = interp.global_object
            testcases = global_object.get(u'testcases')

            testcount = testcases.get(u'length').ToInt32()

            run_test_func = global_object.get(u'run_test')

            test_results = []

            for number in xrange(testcount):
                w_test_number = _w(number)
                result_obj = run_test_func.Call(args=[w_test_number])
                result_passed = result_obj.get(u'passed').to_boolean()
                result_reason = str(result_obj.get(u'reason').to_string())
                test_results.append({'number': number, 'passed': result_passed, 'reason': result_reason})

            return test_results

        if self.do_compile:
            if self.compiled_interpreter is None:
                from rpython.translator.c.test.test_genc import compile
                self.compiled_interpreter = compile(f, [str])
            return self.compiled_interpreter
        else:
            return f

    def get_results(self, test_file):
        interp = self.get_interp()
        return interp(test_file)


class JSTestFile(pytest.File):
    def __init__(self, fspath, parent=None, config=None, session=None):
        super(JSTestFile, self).__init__(fspath, parent, config, session)
        self.name = self.fspath.purebasename

    def collect(self):
        if self.session.config.getvalue("ecma") is not True:
            pytest.skip("ECMA tests disabled, run with --ecma")
        if self.name in SKIP:
            pytest.skip()

        do_compile = self.session.config.getvalue("ecma-compile")
        interp = InterpreterResults(do_compile)

        try:
            results = interp.get_results(str(self.fspath))
        except ParseError, e:
            raise Failed(msg=e.nice_error_message(filename=str(self.fspath)))  # excinfo=None)
        except JsException, e:
            raise Failed(msg="Javascript Error: " + str(e))  # excinfo=py.code.ExceptionInfo())

        for test_result in results:
            number = test_result.get('number')
            passed = test_result.get('passed')
            reason = test_result.get('reason')
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

        # __tracebackhide__ = True
        if passed is False:
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
