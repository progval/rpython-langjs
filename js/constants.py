from rpython.rlib.rsre.rsre_re import compile

num_lit_exp = r'(?:[+-]?((?:(?:\d+)(?:\.\d*)?)|Infinity|(?:\.[0-9]+))(?:[eE][\+\-]?[0-9]*)?)'
num_lit_rexp = compile(num_lit_exp)
num_rexp = compile(r'^%s$' % num_lit_exp)
hex_rexp = compile(r'^0[xX]([\dA-Fa-f]+)$')
oct_rexp = compile(r'^0([0-7]+)$')
