import py
from test.test_interp import assertv


@py.test.mark.xfail
def test_variable_deletion():
    assertv("var x = 3; delete this.x;", False)
    assertv("x = 3; delete this.x;", True)
    assertv("var x = 3; delete this.x; x", 3)
