
from test.test_interp import assertp

def test_infinity_nan(capsys):
    assertp('print(1/0)', 'Infinity', capsys)
    assertp('print(0/0)', 'NaN', capsys)
    assertp('print(-1/0)', '-Infinity', capsys)

def test_overflow_int_to_float(capsys):
    assertp('print(1e200)', '1e+200', capsys)
