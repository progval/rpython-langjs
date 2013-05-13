from test.test_interp import assertv, assertp


def test_sort(capsys):
    assertp("var x = [5,2]; print(x.sort());", '2,5', capsys)
    assertp("var x = [1,2,3]; print(x.sort());", '1,2,3', capsys)
    assertp("var x = [4,3,2,1]; print(x.sort());", '1,2,3,4', capsys)


def test_array_push(capsys):
    assertv("var x = []; x.push(42); x.length;", 1)
    assertv("var x = []; x.push(42); x[0];", 42)
    assertv("var x = [1,2,3]; x.push(42); x[3];", 42)
    assertp("var x = []; x.push(4); x.push(3); x.push(2); x.push(1); print(x)", '4,3,2,1', capsys)


def test_array_pop():
    assertv("var x = [4,3,2,1]; x.pop(); x.length;", 3)
    assertv("var x = [4,3,2,1]; x.pop();", 1)
    assertv("var x = [4,3,2,1]; x.pop(); x.pop(); x.pop(); x.pop();", 4)
    assertv("var x = [4,3,2,1]; x.pop(); x.pop(); x.pop(); x.pop(); x.length", 0)


def test_array_length():
    assertv("var x = []; x.length;", 0)
    assertv("var x = [1,2,3]; x.length;", 3)
    assertv("var x = []; x[0] = 1; x[1] = 2; x[2] = 3; x.length;", 3)
    assertv("var x = []; x[2] = 3; x.length;", 3)


def test_make_array_index():
    from js.jsobj import make_array_index, NOT_ARRAY_INDEX
    assert make_array_index('12345') == 12345
    assert make_array_index(u'12345') == 12345
    assert make_array_index('12a45') == NOT_ARRAY_INDEX
    assert make_array_index('012345') == 12345
    assert make_array_index('') == NOT_ARRAY_INDEX
    assert make_array_index(' ') == NOT_ARRAY_INDEX
    assert make_array_index('x') == NOT_ARRAY_INDEX
    assert make_array_index('abc123') == NOT_ARRAY_INDEX
