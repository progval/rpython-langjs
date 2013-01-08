function _run(name, func) {
    var d = Date.now();
    func();
    print(name + ': ' + (Date.now() - d));
}

function loop1a() {
  var x = 0;
  while(x < 10000000) {
      x += 1;
  }
}

function loop1() {
  var x = 0;
  function f() {
      while(x < 10000000) {
          x += 1;
      }
  }
  f();
}

function loop2() {
  var x = {i:0};
  function f() {
    while(x.i < 10000000) {
      x.i = x.i + 1;
    }
  }
  f();
}

function loop2a() {
  function f() {
    var x = {i:0};
    while(x.i < 10000000) {
      x.i = x.i + 1;
    }
  }
  f();
}

function loop3() {
  var x = {i:0};
  function f() {
    while(x.i < 10000000) {
      x = {i:x.i + 1};
    }
  }
  f();
}

function loop3a() {
  function f() {
    var x = {i:0};
    while(x.i < 10000000) {
      x = {i:x.i + 1};
    }
  }
  f();
}

function loop4() {
  function g(x) {return x + 1;}
  var x = 0;
  function f() {
      while(x < 10000000) {
          x = g(x);
      }
  }
  f();
}

function loop4a() {
  function f() {
      function g(x) {return x + 1;}
      var x = 0;
      while(x < 10000000) {
          x = g(x);
      }
  }
  f();
}

function loop5() {
    for(var i = 0; i < 10000000; i++) {
        i;
    }
}

_run('loop1', loop1);
_run('loop1 local', loop1a);
_run('loop2', loop2);
_run('loop2 local', loop2a);
_run('loop3', loop3);
_run('loop3 local', loop3);
_run('loop4', loop4);
_run('loop4 local', loop4);
_run('loop5', loop5);
