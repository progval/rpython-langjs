import py

xfail = py.test.mark.xfail


@xfail
def test_simple():
    from js.jscode import JsCode
    bytecode = JsCode()
    bytecode.emit('LOAD_FLOATCONSTANT', 2)
    bytecode.emit('LOAD_FLOATCONSTANT', 4)
    bytecode.emit('ADD')

    from js.execution_context import ExecutionContext

    from js.functions import JsExecutableCode
    f = JsExecutableCode(bytecode)

    ctx = ExecutionContext()
    res = f.run(ctx)
    value = res.value
    assert value.ToNumber() == 6.0


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
    from js.object_space import _w

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


def asserte(code, exception):
    from js.interpreter import Interpreter
    jsint = Interpreter()
    py.test.raises(exception, jsint.run_src, code)


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


def test_array_initializer(capsys):
    assertp("""
    x = [];
    print(x);
    print(x.length)
    """, '\n0', capsys)


def test_throw(capsys):
    from js.exception import JsThrowException
    asserte("throw(3);", JsThrowException)


def test_group():
    assertv("(2+1);", 3)


def test_comma():
    assertv("(500,3);", 3)


def test_block(capsys):
    assertp("{print(5);}", '5', capsys)
    assertp("{3; print(5);}", '5', capsys)


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


def test_while(capsys):
    assertp("""
    i = 0;
    while (i<3) {
        print(i);
        i++;
    }
    print(i);
    """, "0\n1\n2\n3", capsys)


def test_assignments():
    assertv("var x = 3; x += 4; x;", 7)
    assertv("x = 8; x -= 3; x;", 5)
    assertv("x = {}; x.x = 3; x.x += 8; x.x", 8 + 3)
    assertv("x = []; x[2] = 1; x[2]++;", 1)
    assertv("x = []; x[2] = 1; x[2]++; x[2]", 2)


def test_object_creation():
    assertv("""
    o = new Object();
    o;
    """, "[object Object]")


def test_var_decl(capsys):
    assertp("print(x); var x;", "undefined", capsys)
    assertp("""
    try {
        print(z);
    }
    catch(e){
        print(e);
    }
    """, "ReferenceError: z is not defined", capsys)


def test_function_name(capsys):
    assertp("""
    function x() {
        print("my name is x");
    }
    x();
    """, "my name is x", capsys)


def test_new_with_function():
    c = """
    x = function() {this.info = 'hello';};
    o = new x();
    o.info;
    """
    assertv(c, "hello")


def test_vars(capsys):
    assertp("var x;x=3; print(x);", "3", capsys)


def test_in(capsys):
    assertp("""
    x = {y:3};
    print("y" in x);
    print("z" in x);
    """, "true\nfalse", capsys)


def test_for(capsys):
    assertp("""
    i = 0;
    for (i; i<3; i++) {
        print(i);
    }
    print(i);
    """, "0\n1\n2\n3", capsys)


def test_eval(capsys):
    assertp("""
    var x = 2;
    eval('x=x+1; print(x); z=2;');
    print(z);
    """, "3\n2", capsys)


def test_eval_syntax_error():
    from js.exception import JsSyntaxError
    asserte("eval('var do =true;');", JsSyntaxError)


def test_arrayobject():
    assertv("""
    var x = new Array();
    x.length == 0;
    """, 'true')


def test_break(capsys):
    assertp("""
    while(1){
        break;
    }
    for(x=0;1==1;x++) {
        break;
    }
    print('out');""", "out", capsys)


def test_typeof():
    assertv("""
    var x = 3;
    typeof x == 'number';
    """, True)
    assertv("typeof x", 'undefined')


def test_semicolon(capsys):
    assertp(';', '', capsys)
    assertv("1", 1)


def test_newwithargs(capsys):
    assertp("""
    var x = new Object(1,2,3,4);
    print(x);
    """, '1', capsys)


def test_increment():
    assertv("""
    var x;
    x = 1;
    x++;
    x;""", 2)


def test_ternaryop():
    assertv("( 1 == 1 ) ? true : false;", True)
    assertv("( 1 == 0 ) ? true : false;", False)


def test_booleanliterals(capsys):
    assertp("""
    var x = false;
    var y = true;
    print(y);
    print(x);""", "true\nfalse", capsys)


def test_unarynot(capsys):
    assertp("""
    var x = false;
    print(!x);
    print(!!x);""", "true\nfalse", capsys)


def test_equals():
    assertv("""
    var x = 5;
    y = z = x;
    y;""", 5)


def test_math_stuff(capsys):
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
    """, '10\n2\nfalse\n3\nNaN\nInfinity\n-Infinity\n3\nnull\n-2', capsys)


def test_globalproperties(capsys):
    assertp("""
    print(NaN);
    print(Infinity);
    print(undefined);
    """, 'NaN\nInfinity\nundefined', capsys)


def test_strangefunc(capsys):
    assertp("""function f1() { var z; var t;}""", '', capsys)
    assertp(""" "'t'"; """, '', capsys)


def test_null():
    from js.object_space import w_Null
    assertv("null;", w_Null)


def test_void(capsys):
    assertp("print(void print('hello'));", "hello\nundefined", capsys)


def test_activationprob(capsys):
    assertp("""
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
    """, '1\n1\n1', capsys)


def test_array_acess(capsys):
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
    """, '1\n2\n1\n2\n3', capsys)


def test_array_length(capsys):
    assertp("""
    var testcases = new Array();
    var tc = testcases.length;
    print('tc'+tc);
    """, 'tc0', capsys)


def test_mod_op(capsys):
    assertp("print(2%2);", '0', capsys)


def test_unary_plus():
    assertv("+1;", 1)
    assertv("-1;", -1)


def test_delete(capsys):
    assertp("""
    x = 0;
    delete x;
    print(this.x)
    """, 'undefined', capsys)
    assertp("""
    var x = {};
    x.y = 1;
    delete x.y;
    print(x.y);
    """, 'undefined', capsys)


def test_forin(capsys):
    assertp("""
    var x = {a:5};
    for(y in x){
        print(y);
    }
    """, 'a', capsys)


def test_forinvar(capsys):
    assertp("""
    var x = {a:5};
    for(var y in x){
        print(y);
    }
    """, 'a', capsys)


def test_stricteq():
    assertv("2 === 2;", True)
    assertv("2 === 3;", False)
    assertv("2 !== 3;", True)
    assertv("2 !== 2;", False)


def test_with(capsys):
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
    """, '4\n2\n3\n4', capsys)


def test_with_expr(capsys):
    assertp("""
    var x = 4;
    with({x:2}) {
        print(x);
    }
    """, '2', capsys)


def test_bitops():
    assertv("2 ^ 2;", 0)
    assertv("2 & 3;", 2)
    assertv("2 | 3;", 3)
    assertv("2 << 2;", 8)
    assertv("4 >> 2;", 1)
    assertv("-2 >> 31", -1)
    assertv("-2 >>> 31;", 1)


def test_for_vararg(capsys):
    assertp("""
    for (var arg = "", i = 0; i < 2; i++) { print(i);}
    """, '0\n1', capsys)


def test_recursive_call():
    assertv("""
    function fact(x) { if (x == 0) { return 1; } else { return fact(x-1)*x; }}
    fact(3);
    """, 6)


def test_function_prototype(capsys):
    assertp("""
    function foo() {}; foo.prototype.bar = function() {};
    """, '', capsys)


def test_function_this(capsys):
    assertp("""
    function foo() {
        print("debug");
        this.bar = function() {};
    };
    var f = new foo();
    f.bar();
    """, 'debug', capsys)


def test_inplace_assign():
    assertv("x=1; x+=1; x;", 2)
    assertv("x=1; x-=1; x;", 0)
    assertv("x=2; x*=2; x;", 4)
    assertv("x=2; x/=2; x;", 1)
    assertv("x=4; x%=2; x;", 0)
    assertv("x=2; x&=2; x;", 2)
    assertv("x=0; x|=1; x;", 1)
    assertv("x=2; x^=2; x;", 0)


def test_not():
    assertv("~1", -2)


def test_delete_member():
    assertv("x = 3; delete this.x", "true")


def test_twoarray(capsys):
    assertp("""
    a1 = new Array();
    a2 = new Array();
    a1[0] = 1;
    print(a1[0]);
    a2[0] = 2;
    print(a1[0]);
    """, '1\n1', capsys)


def test_functionjs():
    assertv("x = Function('return 1'); x()", 1)


def test_octal_and_hex():
    assertv("010;", 8)
    assertv("0xF", 15)


def test_switch():
    assertv("""
    x = 1;
    switch(x){
        case 1: 15; break;
        default: 30;
    };""", 15)
    assertv("""
    x = 0;
    switch(x){
        case 1: 15; break;
        default: 30;
    };""", 30)


def test_autoboxing():
    assertv("'abc'.charAt(0)", 'a')
    assertv("true.toString()", 'true')
    assertv("x=5; x.toString();", '5')


def test_proper_prototype_inheritance():
    assertv("""
    Object.prototype.my = function() {return 1};
    x = {};
    x.my();
    """, 1)
    assertv("""
    Function.prototype.my = function() {return 1};
    function x () {};
    x.my();
    """, 1)


def test_new_without_args_really():
    assertv("var x = new Boolean; x.toString();", 'false')


def test_pypy_repr():
    assertv("pypy_repr(3);", 'W_IntNumber(3)')
    # See optimization on astbuilder.py for a reason to the test below
    assertv("pypy_repr(3.0);", 'W_IntNumber(3)')
    assertv("pypy_repr(3.5);", 'W_FloatNumber(3.5)')
    import sys
    assertv("x=" + str(sys.maxint >> 1) + "; pypy_repr(x*x);", 'W_FloatNumber(2.12676479326e+37)')


def test_number(capsys):
    assertp("print(Number(void 0))", "NaN", capsys)
    assertp("""
    function MyObject( value ) {
      this.value = value;
      this.valueOf = new Function( "return this.value" );
    }
    print (Number(new MyObject(100)));
    """, "100", capsys)


def test_decrement():
    assertv("""
    var x = 2;
    x--;
    x;""", 1)


def test_member_increment():
    assertv("var x = {y:1}; x.y++; x.y;", 2)
    assertv("var x = {y:1}; x.y++;", 1)


def test_member_decrement():
    assertv(" var x = {y:2}; x.y--; x.y;", 1)
    assertv(" var x = {y:2}; x.y--;", 2)


def test_member_preincrement():
    assertv("var x = {y:1}; ++x.y; x.y;", 2)
    assertv("var x = {y:1}; ++x.y;", 2)


def test_member_predecrement():
    assertv("var x = {y:2}; --x.y; x.y;", 1)
    assertv("var x = {y:2}; --x.y;", 1)


def test_member_sub():
    assertv("var x = {y:10}; x.y-=5; x.y", 5)
    assertv("var x = {y:10}; x.y-=5;", 5)


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
    assertv(switch_test_code(0), 42)
    assertv(switch_test_code(1), 1)
    assertv(switch_test_code(2), 2)
    assertv(switch_test_code(3), 42)


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
    assertv(switch_no_default_test_code(0), 42)
    assertv(switch_no_default_test_code(1), 2)


def test_member_bitxor():
    assertv('var i = {x:0}; i.x^=0; i.x;', 0)
    assertv('var i = {x:0}; i.x^=0;', 0)
    assertv('var i = {x:0}; i.x^=1; i.x;', 1)
    assertv('var i = {x:0}; i.x^=1;', 1)
    assertv('var i = {x:1}; i.x^=0; i.x;', 1)
    assertv('var i = {x:1}; i.x^=0;', 1)
    assertv('var i = {x:1}; i.x^=1; i.x;', 0)
    assertv('var i = {x:1}; i.x^=1;', 0)


def test_member_bitand():
    assertv('var i = {x:0}; i.x&=0; i.x;', 0)
    assertv('var i = {x:0}; i.x&=0;', 0)
    assertv('var i = {x:0}; i.x&=1; i.x;', 0)
    assertv('var i = {x:0}; i.x&=1;', 0)
    assertv('var i = {x:1}; i.x&=0; i.x;', 0)
    assertv('var i = {x:1}; i.x&=0;', 0)
    assertv('var i = {x:1}; i.x&=1; i.x;', 1)
    assertv('var i = {x:1}; i.x&=1;', 1)


def test_member_bitor():
    assertv('var i = {x:0}; i.x|=0; i.x;', 0)
    assertv('var i = {x:0}; i.x|=0;', 0)
    assertv('var i = {x:0}; i.x|=1; i.x;', 1)
    assertv('var i = {x:0}; i.x|=1;', 1)
    assertv('var i = {x:1}; i.x|=0; i.x;', 1)
    assertv('var i = {x:1}; i.x|=0;', 1)
    assertv('var i = {x:1}; i.x|=1; i.x;', 1)
    assertv('var i = {x:1}; i.x|=1;', 1)


def test_store_bitrsh():
    assertv('var i = 1; i>>=0; i;', 1)
    assertv('var i = 1; i>>=0;', 1)
    assertv('var i = 2; i>>=1; i;', 1)
    assertv('var i = 2; i>>=1;', 1)
    assertv('var i = 4; i>>=1; i;', 2)
    assertv('var i = 4; i>>=1;', 2)
    assertv('var i = 4; i>>=2; i;', 1)
    assertv('var i = 4; i>>=2;', 1)
    assertv('var i = 4; i>>=3; i;', 0)
    assertv('var i = 4; i>>=3;', 0)


def test_loop_continue():
    assertv("""
      i = 0;
      n = 0;
      while (i < 3) {
         i++;
         if (i == 1)
            continue;
         n += i;
      }
      n;
    """, 5)
    assertv("""
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
    """, 80)
    assertv("""
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
    """, 400)


def test_partial_for_loop():
    assertv("""
    var i = 0;
    for(;;){
      i++;
      if(i == 2)
          break;
    }
    i;
    """, 2)
    assertv("""
    var i = 0;
    for(;;i++){
      if(i == 2)
          break;
    }
    i;
    """, 2)
    assertv("""
    var i = 0;
    for(i = 2;;){
      if(i == 2)
          break;
      i = 99;
    }
    i;
    """, 2)
    assertv("""
    var i = 0;
    for(;i <= 1;){
        i++;
    }
    i;
    """, 2)


def test_compare_string_null():
    assertv("""
    var x;
    if('a' == null){
        x = true;
    } else {
        x = false;
    }
    x;
    """, False)


def test_math_random():
    assertv("var x = Math.random(); var y = Math.random(); x == y;", False)


def test_math_min():
    assertv("Math.min(1, 2);", 1)
    assertv("Math.min(0, 2);", 0)
    assertv("Math.min(-1, 1);", -1)


def test_math_max():
    assertv("Math.max(1, 2);", 2)
    assertv("Math.max(0, 2);", 2)
    assertv("Math.max(-1, 1);", 1)


def test_date_get_time():
    assertv("var i = new Date(); i.valueOf() == i.getTime()", True)


def test_declare_local_var():
    assertv("""
    function f() {
        var i = 4;
        function g() {
            return i + 8;
        }
        return g();
    }
    f();
    """, 12)
    assertv("""
    function f() {
        var i;
        function g() {
            i = 4;
            return 8;
        }
        return g() + i;
    }
    f();
    """, 12)


def test_empty_function_with_params():
    assertv("x = function(x) { }; x(); false", False)


def test_params_order(capsys):
    assertp("function f(a, b, c, d) { return print([a, b, c, d]) }; f(1,2,3,4)", "1,2,3,4", capsys)
    assertp("function f(z, y, x, w) { return print([z, y, x, w]) }; f(1,2,3,4)", "1,2,3,4", capsys)
    assertp("function f(n, d, e, a) { return print([n, d, e, a]) }; f(1,2,3,4)", "1,2,3,4", capsys)


def test_function_without_implicit_return_value():
    assertv("""
    function f(a) {
        if(a != null)
            if(true) this.foo(a);
    }
    f(null);
    1;
    """, 1)


def test_boolean_constructor():
    assertv("typeof Boolean(true)", 'boolean')
    assertv("typeof new Boolean(true)", 'object')


def test_return_trycatch():
    assertv("function f() { try { return 1; } catch(e) { return -1; } }; f()", 1)
    assertv("function f() { try { throw('foo'); return 1; } catch(e) { return -1; } }; f()", -1)
    assertv("function f() { try { throw('foo'); return 1; } catch(e) { return -1; } finally { return 0; } }; f()", 0)
    assertv("function f() { try { throw('foo'); return 1; } finally { return 0; } }; f()", 0)


def test_try_catch_loop():
    assertv("try { x = 1; } catch(e) { }; 0", 0)
    assertv("function g() { throw(1) } function f() { for(i=0; i < 3; i++) { try { x = g(); } catch(e) { } } } f(); 0", 0)
    assertv("function f() { for(i=0; i < 3; i++) { try { x = 1; } catch(e) { } } } f(); 0", 0)


def test_instanceof():
    assertv("function f(){this.a = 1;}; x = new f(); x instanceof f;", True)
    assertv("function f(){this.a = 1;}; function g(){this.a = b;}; x = new f(); x instanceof g;", False)


def test_repeated_for_loop():
    assertv("var a = 0; for(var x = 0; x < 10; x++){for(var y = 0; y < 10; y++) {a += y}}; a;", 450)


def test_repeated_for_in():
    assertv("var a = [1,2,3]; var b = 0; for(var x = 0; x < 10; x++){for(var y in a) {b += y}}; b;", '0012012012012012012012012012012')
