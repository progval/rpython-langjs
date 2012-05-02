import py
#from js import interpreter
#from js.operations import IntNumber, FloatNumber, Position, Plus
#from js.jsobj import W_Root, w_Null, W___Root
#from js.execution import ThrowException
#from js.jscode import JsCode
#from js.baseop import AbstractEC

def test_simple():
    from js.jscode import JsCode
    bytecode = JsCode()
    bytecode.emit('LOAD_FLOATCONSTANT', 2)
    bytecode.emit('LOAD_FLOATCONSTANT', 4)
    bytecode.emit('ADD')
    bytecode.emit('POP')

    from js.execution_context import ExecutionContext

    from js.functions import JsExecutableCode
    f = JsExecutableCode(bytecode)

    from js.execution_context import ExecutionContext
    ctx = ExecutionContext()
    res = f.run(ctx)

    assert res.ToNumber() == 6.0

def assertp(code, prints, captured):
    out, err = captured.readouterr()

    from js.interpreter import Interpreter
    jsint = Interpreter()
    jsint.run_src(code)
    out, err = captured.readouterr()
    assert out.strip() == prints.strip()
    #l = []
    #import js.builtins_global
    #js.builtins_global.writer = l.append
    #jsint = interpreter.Interpreter()
    #ctx = jsint.w_Global
    #try:
        #jsint.run(interpreter.load_source(code, ''))
    #except ThrowException, excpt:
        #l.append("uncaught exception: "+str(excpt.exception.to_string()))
    #print l, prints
    #if isinstance(prints, list):
        #assert l == prints
    #else:
        #assert l[0] == prints

def assertv(code, value):
    from js.interpreter import Interpreter
    from js.jsobj import _w

    jsint = Interpreter()
    ret_val = jsint.run_src(code)

    assert ret_val == _w(value)

    #try:
        #code_val = jsint.run_src(code)
    #except ThrowException, excpt:
        #code_val = excpt.exception
    #print code_val, value
    #if isinstance(value, W___Root):
        #assert AbstractEC(jsint.global_context, code_val, value) == True
    #elif isinstance(value, bool):
        #assert code_val.ToBoolean() == value
    #elif isinstance(value, int):
        #assert code_val.ToInt32() == value
    #elif isinstance(value, float):
        #assert code_val.ToNumber() == value
    #else:
        #assert code_val.to_string() == value

def asserte(code, value):
    pass
    #jsint = interpreter.Interpreter()
    #py.test.raises(value, 'jsint.run(interpreter.load_source(code, ""))')

def test_interp_parse(capsys):
    assertv("1+1;", 2)
    assertp("print(1+2+3); print(1);", "6\n1", capsys)
    assertp("print(1,2,3);", "1,2,3", capsys)

def test_var_assign():
    assertv("x=3;x;", 3)
    assertv("x=3;y=4;x+y;", 7)

def test_minus():
    assertv("2-1;", 1)

def test_string_var():
    assertv('"sss";', 'sss')

def test_string_concat(capsys):
    assertp('x="xxx"; y="yyy"; print(x+y);', "xxxyyy", capsys)

def test_string_num_concat(capsys):
    assertp('x=4; y="x"; print(x+y, y+x);', "4x,x4", capsys)

def test_to_string(capsys):
    assertp("x={}; print(x);", "[object Object]", capsys)

def test_object_access(capsys):
    assertp("x={d:3}; print(x.d);", "3", capsys)
    assertp("x={d:3}; print(x.d.d);", "undefined", capsys)
    assertp("x={d:3, z:4}; print(x.d-x.z);", "-1", capsys)

def test_object_access_index(capsys):
    assertp('x={d:"x"}; print(x["d"]);', 'x', capsys)

def test_function_prints(capsys):
    assertp('x=function(){print(3);}; x();', '3', capsys)

def test_function_returns(capsys):
    assertv('x=function(){return 1;}; x()+x();', 2)
    assertp('function x() { return; };', '', capsys)
    assertv('function x() { d=2; return d;}; x()', 2)

def test_var_declaration():
    assertv('var x = 3; x;', 3)
    assertv('var x = 3; x+x;', 6)

def test_var_scoping(capsys):
    assertp("""
    var y;
    var p;
    p = 0;
    function x () {
        var p;
        p = 1;
        y = 3;
        return y + z;
    };
    var z = 2;
    print(x(), y, p);
    """, "5,3,0", capsys)

def test_var_scoping_default_global():
    assertv('d = 1; function x() { d=2;}; x(); d;', 2)
    assertv('d = 1; function x() { var d=2;}; x(); d;', 1)
    assertv('function x() { d=2;}; x(); d;', 2)
    assertv('var d = 1; function x() { d=2; }; x(); d;', 2)
    assertv('function x() { d=2;}; function y() { return d; }; x(); y();', 2)
    assertv('var d; function x() { d=2;}; function y() { return d; }; x(); y();', 2)

def test_function_args():
    assertv("""
    x = function (t,r) {
       return t+r;
    };
    x(2,3);
    """, 5)

def test_function_less_args(capsys):
    assertp("""
    x = function (t, r) {
        return t + r;
    };
    print(x(2));
    """, "NaN", capsys)

def test_function_more_args():
    assertv("""
    x = function (t, r) {
        return t + r;
    };
    x(2,3,4);
    """, 5)

def test_function_has_var():
    assertv("""
    x = function () {
        var t = 'test';
        return t;
    };
    x();
    """, 'test')

def test_function_arguments():
    assertv("""
    x = function () {
        r = arguments[0];
        t = arguments[1];
        return t + r;
    };
    x(2,3);
    """, 5)


def test_index():
    assertv("""
    x = {1:"test"};
    x[1];
    """, 'test')

def test_print_object(capsys):
    assertp("""
    x = {1:"test"};
    print(x);
    """, "[object Object]", capsys)
    assertp("""
    print(Object);
    """, "function Object() { [native code] }", capsys)
    assertp("""
    print(Object.prototype);
    """, "[object Object]", capsys)

@py.test.mark.xfail
def test_array_initializer(capsys):
    assertp("""
    x = [];
    print(x);
    print(x.length)
    """, '\n0', capsys)

@py.test.mark.xfail
def test_throw(capsys):
    assertp("throw(3);", "uncaught exception: 3", capsys)

def test_group():
    assertv("(2+1);", 3)

def test_comma():
    assertv("(500,3);", 3)

def test_block(capsys):
    assertp("{print(5);}", '5', capsys)
    assertp("{3; print(5);}", '5', capsys)

@py.test.mark.xfail
def test_try_catch_finally(capsys):
    assertp("""
    try {
        throw(3);
    }
    catch (x) {
        print(x);
    }
    """, "3", capsys)
    assertp("""
    try {
        throw(3);
    }
    catch (x) {
        print(x);
    }
    finally {
        print(5);
    }
    """, "3\n5", capsys)

def test_if_then(capsys):
    assertp("""
    if (1) {
        print(1);
    }
    """, "1", capsys)

def test_if_then_else(capsys):
    assertp("""
    if (0) {
        print(1);
    } else {
        print(2);
    }
    """, "2", capsys)

def test_compare():
    assertv("1>0;", True)
    assertv("0>1;", False)
    assertv("0>0;", False)
    assertv("1<0;", False)
    assertv("0<1;", True)
    assertv("0<0;", False)
    assertv("1>=0;", True)
    assertv("1>=1;", True)
    assertv("1>=2;", False)
    assertv("0<=1;", True)
    assertv("1<=1;", True)
    assertv("1<=0;", False)
    assertv("0==0;", True)
    assertv("1==1;", True)
    assertv("0==1;", False)
    assertv("0!=1;", True)
    assertv("1!=1;", False)
    assertv("1===1;", True)
    assertv("1!==1;", False)

def test_string_compare():
    assertv("'aaa' > 'a';", True)
    assertv("'aaa' < 'a';", False)
    assertv("'a' > 'a';", False)

def test_binary_opb(capsys):
    assertp("print(0||0); print(1||0);", "0\n1", capsys)
    assertp("print(0&&1); print(1&&1);", "0\n1", capsys)

def test_while():
    assertp("""
    i = 0;
    while (i<3) {
        print(i);
        i++;
    }
    print(i);
    """, ["0","1","2","3"])

def test_assignments():
    yield assertv, "var x = 3; x += 4; x;", 7
    yield assertv, "x = 8; x -= 3; x;", 5
    yield assertv, "x = {}; x.x = 3; x.x += 8; x.x", 8+3
    yield assertv, "x = []; x[2] = 1; x[2]++;", 1
    yield assertv, "x = []; x[2] = 1; x[2]++; x[2]", 2

def test_object_creation():
    yield assertv, """
    o = new Object();
    o;
    """, "[object Object]"

def test_var_decl():
    yield assertp, "print(x); var x;", "undefined"
    yield assertp, """
    try {
        print(z);
    }
    catch (e) {
        print(e);
    }
    """, "ReferenceError: z is not defined"

def test_function_name():
    assertp("""
    function x() {
        print("my name is x");
    }
    x();
    """, "my name is x")

def test_new_with_function():
    c= """
    x = function() {this.info = 'hello';};
    o = new x();
    o.info;
    """
    assertv(c, "hello")

def test_vars():
    assertp("""
    var x;x=3; print(x);""", ["3"])

def test_in():
    assertp("""
    x = {y:3};
    print("y" in x);
    print("z" in x);
    """, ["true", "false"])

def test_for():
    assertp("""
    i = 0;
    for (i; i<3; i++) {
        print(i);
    }
    print(i);
    """, ["0","1","2","3"])

#def test_eval():
    #yield assertp, """
    #var x = 2;
    #eval('x=x+1; print(x); z=2;');
    #print(z);
    #""", ["3","2"]
    #yield asserte, "eval('var do =true;');", ThrowException

def test_arrayobject():
    assertv("""var x = new Array();
    x.length == 0;""", 'true')

def test_break():
    assertp("""
    while(1){
        break;
    }
    for(x=0;1==1;x++) {
        break;
    }
    print('out');""", "out")

def test_typeof():
    assertv("""
    var x = 3;
    typeof x == 'number';
    """, True)
    assertv("""
    typeof x
    """, 'undefined')

def test_semicolon():
    assertp(';', [])

def test_newwithargs():
    assertp("""
    var x = new Object(1,2,3,4);
    print(x);
    """, '1')

def test_increment():
    assertv("""
    var x;
    x = 1;
    x++;
    x;""", 2)

def test_ternaryop():
    yield assertv, "( 1 == 1 ) ? true : false;", True
    yield assertv, "( 1 == 0 ) ? true : false;", False

def test_booleanliterals():
    assertp("""
    var x = false;
    var y = true;
    print(y);
    print(x);""", ["true", "false"])

def test_unarynot():
    assertp("""
    var x = false;
    print(!x);
    print(!!x);""", ["true", "false"])

def test_equals():
    assertv("""
    var x = 5;
    y = z = x;
    y;""", 5)

def test_math_stuff():
    assertp("""
    var x = 5;
    var z = 2;
    print(x*z);
    print(4/z);
    print(isNaN(z));
    print(Math.abs(z-x));
    print(Number.NaN);
    print(Number.POSITIVE_INFINITY);
    print(Number.NEGATIVE_INFINITY);
    print(Math.floor(3.2));
    print(null);
    print(-z);
    """, ['10', '2', 'false', '3', 'NaN', 'Infinity', '-Infinity',
    '3', 'null', '-2'])

def test_globalproperties():
    assertp( """
    print(NaN);
    print(Infinity);
    print(undefined);
    """, ['NaN', 'Infinity', 'undefined'])

def test_strangefunc():
    assertp("""function f1() { var z; var t;}""", [])
    assertp(""" "'t'"; """, [])

def test_null():
    assertv("null;", w_Null)

def test_void():
    assertp("print(void print('hello'));",
                        ["hello", "undefined"])

def test_activationprob():
    assertp( """
    function intern (int1){
        print(int1);
        return int1;
    }
    function x (v1){
        this.p1 = v1;
        this.p2 = intern(this.p1);
    }
    var ins = new x(1);
    print(ins.p1);
    print(ins.p2);
    """, ['1','1', '1'])

def test_array_acess():
    assertp("""
    var x = new Array();
    x[0] = 1;
    print(x[0]);
    x[x[0]] = 2;
    print(x[1]);
    x[2] = x[0]+x[1];
    for(i=0; i<3; i++){
        print(x[i]);
    }
    """, ['1','2', '1', '2', '3'])

def test_array_length():
    assertp("""
    var testcases = new Array();
    var tc = testcases.length;
    print('tc'+tc);
    """, 'tc0')

def test_mod_op():
    assertp("print(2%2);", '0')

def test_unary_plus():
    assertp("print(+1);", '1')

def test_delete():
    assertp("""
    x = 0;
    delete x;
    print(this.x)
    """, 'undefined')
    assertp("""
    var x = {};
    x.y = 1;
    delete x.y;
    print(x.y);
    """, 'undefined')

def test_forin():
    assertp("""
    var x = {a:5};
    for(y in x){
        print(y);
    }
    """, ['5',])

def test_forinvar():
    assertp("""
    var x = {a:5};
    for(var y in x){
        print(y);
    }
    """, ['5',])

def test_stricteq():
    yield assertv, "2 === 2;", True
    yield assertv, "2 === 3;", False
    yield assertv, "2 !== 3;", True
    yield assertv, "2 !== 2;", False

def test_with():
    assertp("""
    var mock = {x:2};
    var x=4;
    print(x);
    try {
        with(mock) {
            print(x);
            throw 3;
            print("not reacheable");
        }
    }
    catch(y){
        print(y);
    }
    print(x);
    """, ['4', '2', '3', '4'])

def test_with_expr():
    assertp("""
    var x = 4;
    with({x:2}) {
        print(x);
    }
    """, ['2'])

def test_bitops():
    yield assertv, "2 ^ 2;", 0
    yield assertv, "2 & 3;", 2
    yield assertv, "2 | 3;", 3
    yield assertv, "2 << 2;", 8
    yield assertv, "4 >> 2;", 1
    yield assertv, "-2 >> 31", -1
    yield assertv, "-2 >>> 31;", 1

def test_for_vararg():
    assertp("""
    for (var arg = "", i = 0; i < 2; i++) { print(i);}
    """, ['0', '1'])

def test_recursive_call():
    assertv("""
    function fact(x) { if (x == 0) { return 1; } else { return fact(x-1)*x; }}
    fact(3);
    """, 6)

def test_function_prototype():
    assertp("""
    function foo() {}; foo.prototype.bar = function() {};
    """, [])


def test_function_this():
    assertp("""
    function foo() {print("debug");this.bar = function() {};};
    var f = new foo();
    f.bar();
    """, 'debug')

def test_inplace_assign():
    yield assertv, "x=1; x+=1; x;", 2
    yield assertv, "x=1; x-=1; x;", 0
    yield assertv, "x=2; x*=2; x;", 4
    yield assertv, "x=2; x/=2; x;", 1
    yield assertv, "x=4; x%=2; x;", 0
    yield assertv, "x=2; x&=2; x;", 2
    yield assertv, "x=0; x|=1; x;", 1
    yield assertv, "x=2; x^=2; x;", 0

def test_not():
    assertv("~1", -2)

def test_delete_member():
    assertv("x = 3; delete this.x", "true")

def test_twoarray():
    assertp("""
    a1 = new Array();
    a2 = new Array();
    a1[0] = 1;
    print(a1[0]);
    a2[0] = 2;
    print(a1[0]);
    """, ['1', '1'])

def test_semicolon():
    assertv("1", 1)

def test_functionjs():
    assertv("x = Function('return 1'); x()", 1)

def test_octal_and_hex():
    yield assertv, "010;", 8
    yield assertv, "0xF", 15

def test_switch():
    yield assertv, """
    x = 1;
    switch(x){
        case 1: 15; break;
        default: 30;
    };""", 15
    yield assertv, """
    x = 0;
    switch(x){
        case 1: 15; break;
        default: 30;
    };""", 30

def test_autoboxing():
    yield assertv, "'abc'.charAt(0)", 'a'
    yield assertv, "true.toString()", 'true'
    yield assertv, "x=5; x.toString();", '5'

def test_proper_prototype_inheritance():
    yield assertv, """
    Object.prototype.my = function() {return 1};
    x = {};
    x.my();
    """, 1
    yield assertv, """
    Function.prototype.my = function() {return 1};
    function x () {};
    x.my();
    """, 1

def test_new_without_args_really():
    assertv("var x = new Boolean; x.toString();", 'false')

def test_pypy_repr():
    yield assertv, "pypy_repr(3);", 'W_IntNumber(3)'
    # See optimization on astbuilder.py for a reason to the test below
    yield assertv, "pypy_repr(3.0);", 'W_IntNumber(3)'
    yield assertv, "pypy_repr(3.5);", 'W_FloatNumber(3.5)'
    import sys
    yield assertv, "x="+str(sys.maxint >> 1)+"; pypy_repr(x*x);", 'W_FloatNumber(2.12676479326e+37)'

def test_number():
    assertp("print(Number(void 0))", "NaN")
    assertp("""
    function MyObject( value ) {
      this.value = value;
      this.valueOf = new Function( "return this.value" );
    }
    print (Number(new MyObject(100)));
    """, "100")

def test_decrement():
    assertv("""
    var x = 2;
    x--;
    x;""", 1)

def test_member_increment():
    yield assertv, "var x = {y:1}; x.y++; x.y;", 2
    yield assertv, "var x = {y:1}; x.y++;", 1

def test_member_decrement():
    yield assertv, " var x = {y:2}; x.y--; x.y;", 1
    yield assertv, " var x = {y:2}; x.y--;", 2

def test_member_preincrement():
    yield assertv, "var x = {y:1}; ++x.y; x.y;", 2
    yield assertv, "var x = {y:1}; ++x.y;", 2

def test_member_predecrement():
    yield assertv, "var x = {y:2}; --x.y; x.y;", 1
    yield assertv, "var x = {y:2}; --x.y;", 1

def test_member_sub():
    yield assertv, "var x = {y:10}; x.y-=5; x.y", 5
    yield assertv, "var x = {y:10}; x.y-=5;", 5

def switch_test_code(x):
    return """
    function f(x) {
      var y;
      switch(x) {
        case 1:
            y = 1;
            break;
        case 2:
            y = 2;
            break;
        case 3:
        default:
            return 42;
      }
      return y;
    };

    f(%(x)s);
    """ % {'x': x}


def test_more_switch():
    yield assertv, switch_test_code(0), 42
    yield assertv, switch_test_code(1), 1
    yield assertv, switch_test_code(2), 2
    yield assertv, switch_test_code(3), 42

def switch_no_default_test_code(x):
    return """
    function f(x) {
      switch(x) {
        case 1:
            return 2;
            break;
      }
      return 42;
    };

    f(%(x)s);
    """ % {'x': x}

def test_switch_no_default():
    yield assertv, switch_no_default_test_code(0), 42
    yield assertv, switch_no_default_test_code(1), 2

def test_member_bitxor():
    yield assertv, 'var i = {x:0}; i.x^=0; i.x;', 0
    yield assertv, 'var i = {x:0}; i.x^=0;', 0
    yield assertv, 'var i = {x:0}; i.x^=1; i.x;', 1
    yield assertv, 'var i = {x:0}; i.x^=1;', 1
    yield assertv, 'var i = {x:1}; i.x^=0; i.x;', 1
    yield assertv, 'var i = {x:1}; i.x^=0;', 1
    yield assertv, 'var i = {x:1}; i.x^=1; i.x;', 0
    yield assertv, 'var i = {x:1}; i.x^=1;', 0

def test_member_bitand():
    yield assertv, 'var i = {x:0}; i.x&=0; i.x;', 0
    yield assertv, 'var i = {x:0}; i.x&=0;', 0
    yield assertv, 'var i = {x:0}; i.x&=1; i.x;', 0
    yield assertv, 'var i = {x:0}; i.x&=1;', 0
    yield assertv, 'var i = {x:1}; i.x&=0; i.x;', 0
    yield assertv, 'var i = {x:1}; i.x&=0;', 0
    yield assertv, 'var i = {x:1}; i.x&=1; i.x;', 1
    yield assertv, 'var i = {x:1}; i.x&=1;', 1

def test_member_bitor():
    yield assertv, 'var i = {x:0}; i.x|=0; i.x;', 0
    yield assertv, 'var i = {x:0}; i.x|=0;', 0
    yield assertv, 'var i = {x:0}; i.x|=1; i.x;', 1
    yield assertv, 'var i = {x:0}; i.x|=1;', 1
    yield assertv, 'var i = {x:1}; i.x|=0; i.x;', 1
    yield assertv, 'var i = {x:1}; i.x|=0;', 1
    yield assertv, 'var i = {x:1}; i.x|=1; i.x;', 1
    yield assertv, 'var i = {x:1}; i.x|=1;', 1

def test_store_bitrsh():
    yield assertv, 'var i = 1; i>>=0; i;', 1
    yield assertv, 'var i = 1; i>>=0;', 1
    yield assertv, 'var i = 2; i>>=1; i;', 1
    yield assertv, 'var i = 2; i>>=1;', 1
    yield assertv, 'var i = 4; i>>=1; i;', 2
    yield assertv, 'var i = 4; i>>=1;', 2
    yield assertv, 'var i = 4; i>>=2; i;', 1
    yield assertv, 'var i = 4; i>>=2;', 1
    yield assertv, 'var i = 4; i>>=3; i;', 0
    yield assertv, 'var i = 4; i>>=3;', 0

def test_loop_continue():
    yield assertv, """
      i = 0;
      n = 0;
      while (i < 3) {
         i++;
         if (i == 1)
            continue;
         n += i;
      }
      n;
    """, 5
    yield assertv, """
      i = 0;
      n = 0;
      while (i < 3) {
         i++;
         if (i == 1)
            continue;
         for(j = 0; j < 10; j++) {
           if (j == 5)
               continue;
           n += j;
         }
      }
      n;
    """, 80
    yield assertv, """
      i = 0;
      n = 0;
      while (i < 3) {
         i++;
         if (i == 1)
            continue;
         for(j = 0; j < 10; j++) {
           if (j == 5)
               continue;
           k = 0;
           while(k < 10) {
             k++;
             if (k % 2 == 0)
                continue;
             n += j;
           }
         }
      }
      n;
    """, 400

def test_partial_for_loop():
    yield assertv, """
    var i = 0;
    for(;;){
      i++;
      if(i == 2)
          break;
    }
    i;
    """, 2
    yield assertv, """
    var i = 0;
    for(;;i++){
      if(i == 2)
          break;
    }
    i;
    """, 2
    yield assertv, """
    var i = 0;
    for(i = 2;;){
      if(i == 2)
          break;
      i = 99;
    }
    i;
    """, 2
    yield assertv, """
    var i = 0;
    for(;i <= 1;){
        i++;
    }
    i;
    """, 2

def test_compare_string_null():
    yield assertv, """
    var x;
    if('a' == null){
        x = true;
    } else {
        x = false;
    }
    x;
    """, False

def test_math_random():
    yield assertv, "var x = Math.random(); var y = Math.random(); x == y;", False

def test_math_min():
    yield assertv, "Math.min(1, 2);", 1
    yield assertv, "Math.min(0, 2);", 0
    yield assertv, "Math.min(-1, 1);", -1

def test_math_max():
    yield assertv, "Math.max(1, 2);", 2
    yield assertv, "Math.max(0, 2);", 2
    yield assertv, "Math.max(-1, 1);", 1

def test_date_get_time():
    yield assertv, "var i = new Date(); i.valueOf() == i.getTime()", True

def test_declare_local_var():
    yield assertv, """
    function f() {
        var i = 4;
        function g() {
            return i + 8;
        }
        return g();
    }
    f();
    """, 12
    yield assertv, """
    function f() {
        var i;
        function g() {
            i = 4;
            return 8;
        }
        return g() + i;
    }
    f();
    """, 12

def test_empty_function_with_params():
    assertv("x = function(x) { }; x(); false", False)
