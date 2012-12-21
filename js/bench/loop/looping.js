function loop0() {
  var x = 0;
  while(x < 10000000) {
      x += 1;
  }
}

function loop1() {
  function f() {
      var x = 0;
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

new BenchmarkSuite('Looping 0', 100000, [
  new Benchmark('Loop', loop0)
]);

new BenchmarkSuite('Looping 1', 100000, [
  new Benchmark('Loop', loop1)
]);

new BenchmarkSuite('Looping 2', 100000, [
  new Benchmark('Loop', loop2)
]);

new BenchmarkSuite('Looping 2a', 100000, [
  new Benchmark('Loop', loop2a)
]);

new BenchmarkSuite('Looping 3', 100000, [
  new Benchmark('Loop', loop3)
]);

new BenchmarkSuite('Looping 3a', 100000, [
  new Benchmark('Loop', loop3a)
]);

new BenchmarkSuite('Looping 4', 100000, [
  new Benchmark('Loop', loop4)
]);

new BenchmarkSuite('Looping 4a', 100000, [
  new Benchmark('Loop', loop4a)
]);
