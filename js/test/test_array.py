from js.test.test_interp import assertv, assertp

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
    assertv("var x = [1,2,3]; x.length;", 3);
    assertv("var x = []; x[0] = 1; x[1] = 2; x[2] = 3; x.length;", 3);
    assertv("var x = []; x[2] = 3; x.length;", 3);
