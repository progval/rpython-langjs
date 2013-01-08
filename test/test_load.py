import py
from test.test_interp import assertv

def test_load():
    pwd = py.path.local(__file__)
    js_file = str(pwd.dirpath('test_load.js'))
    assertv("load('"+js_file+"'); x;", 1)
