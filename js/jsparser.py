from pypy.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function
from pypy.rlib.parsing.parsing import ParseError, Rule
import py
import sys

sys.setrecursionlimit(10000)

GFILE = py.path.local(__file__).dirpath().join('jsgrammar.txt')
try:
    t = GFILE.read(mode='U')
    regexs, rules, ToAST = parse_ebnf(t)
except ParseError,e:
    print e.nice_error_message(filename=str(GFILE),source=t)
    raise

NFILE = py.path.local(__file__).dirpath().join('jsgrammar_numeric.txt')
try:
    n = NFILE.read(mode='U')
    n_regexs, n_rules, n_ToAST = parse_ebnf(n)
except ParseError,e:
    print e.nice_error_message(filename=str(GFILE),source=t)
    raise

parsef = make_parse_function(regexs, rules, eof=True)
def parse(code):
    t = parsef(code)
    return ToAST().transform(t)

parsen = make_parse_function(n_regexs, n_rules, eof=True)
def parse_numbe(code):
    t = parsen(code)
    return n_ToAST().transform(t)
