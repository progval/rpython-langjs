function _run(file) {
    var d = Date.now();
    load(file);
    print(file + ': ' + (Date.now() - d));
}

_run("t/3d-cube.js");
//load("t/3d-morph.js");
//load("t/3d-raytrace.js");
_run("t/access-binary-trees.js");
_run("t/access-fannkuch.js");
_run("t/access-nbody.js");
//_run("t/access-nsieve.js");
_run("t/bitops-3bit-bits-in-byte.js");
//_run("t/bitops-bits-in-byte.js");
_run("t/bitops-bitwise-and.js");
//_run("t/bitops-nsieve-bits.js");
_run("t/controlflow-recursive.js");
//load("t/crypto-aes.js");
_run("t/crypto-md5.js");
_run("t/crypto-sha1.js");
//load("t/date-format-tofte.js");
//load("t/date-format-xparb.js");
_run("t/math-cordic.js");
_run("t/math-partial-sums.js");
_run("t/math-spectral-norm.js");
//load("t/regexp-dna.js");
_run("t/string-base64.js");
load("t/string-fasta.js");
//load("t/string-tagcloud.js");
//load("t/string-unpack-code.js");
//load("t/string-validate-input.js");
