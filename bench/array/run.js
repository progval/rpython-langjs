function _run(name, func) {
    var d = Date.now();
    func();
    print(name + ': ' + (Date.now() - d));
}

var max_a = 1000000;

function array1() {
  var x = 0;
  var a = [];
  while(x < max_a) {
      a[x] = x;
      x += 1;
  }
  return a;
}

function array2() {
  var x = 0;
  var a = [];
  while(x < max_a) {
      a[x*2] = x;
      x += 1;
  }
  return a;
}

function array3() {
  var x = 0;
  var a = [];
  while(x < max_a) {
    var idx = Math.floor(Math.random() * max_a);
    a[idx] = idx;
    x += 1;
  }
  return a;
}

function array4() {
  var x = 0;
  var a = [];
  while(x < max_a) {
    a.push(x);
    x += 1;
  }
  x = 0;
  while(x < max_a) {
    a.pop();
    x += 1;
  }
  return a;
}

function array5() {
  var x = 0;
  var a = [];
  while(x < max_a) {
    a.push(x);
    x += 1;
  }
  x = 0;
  while(x < max_a) {
    a.pop();
    x += 1;
  }
  return a;
}

function array6() {
  var x = 0;
  var a = [];
  while(x < 100) {
    while(a.length < max_a) {
      a.push(x);
    }
    while(a.length > 0) {
      a.pop();
    }
    x += 1;
  }
  return a;
}

function arrayXXX() {
  var x = 0;
  var a = [];
  var b = [];
  while(x < 100) {
      a[x] = x;
      x += 1;
  }
  x = 0;
  while(a.length > 0) {
    var a_idx = Math.floor(Math.random() * a.length);
    var b_idx = a.splice(a_idx, 1);
    b[b_idx] = b_idx;
  }
  return b;
}

_run('array1', array1);
_run('array2', array2);
_run('array3', array3);
_run('array4', array4);
_run('array5', array5);
//_run('array6', array6);
