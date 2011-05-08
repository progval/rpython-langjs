from js.test.test_interp import assertv, assertp

def test_array_push():
    yield assertv, "var x = []; x.push(42); x.length;", 1
    yield assertv, "var x = []; x.push(42); x[0];", 42
    yield assertv, "var x = [1,2,3]; x.push(42); x[3];", 42
    yield assertp, "var x = []; x.push(4); x.push(3); x.push(2); x.push(1); print(x)", '4,3,2,1'
