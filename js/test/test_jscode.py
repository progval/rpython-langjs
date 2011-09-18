import py

def assert_code_size(*args):
    from js.jscode import JsCode
    b = JsCode()
    size = args[-1]

    for bytecode in args[:-1]:
        if type(bytecode) == tuple:
            a = bytecode
        else:
            a = (bytecode,)
        b.emit(*a)

    assert b.estimated_stack_size() == size

class TestJsCodeSizeEstimation(object):
    def test_estimate_size_empty_code(self):
        assert_code_size(0)

    def test_estimate_size(self):
        yield assert_code_size, ('LOAD_INTCONSTANT', 1), 'POP', 1
        yield assert_code_size, ('LOAD_INTCONSTANT', 1), 'POP', 'POP', 1
        yield assert_code_size, ('LOAD_INTCONSTANT', 1), ('LOAD_INTCONSTANT', 2), 'ADD', 2
        yield assert_code_size, ('LOAD_LIST', 5), 0
        yield assert_code_size, ('LOAD_ARRAY', 5), 0
        yield assert_code_size, ('LOAD_LOCAL', 1), ('LOAD_LOCAL', 1), ('LOAD_LOCAL', 1), ('LOAD_ARRAY', 3), 3
        yield assert_code_size,\
            ('LOAD_LOCAL', 1), ('LOAD_LOCAL', 1), ('LOAD_LOCAL', 1),\
            ('LOAD_ARRAY', 3),\
            ('LOAD_LOCAL', 1), ('LOAD_LOCAL', 1), ('LOAD_LOCAL', 1), ('LOAD_LOCAL', 1),\
            5
