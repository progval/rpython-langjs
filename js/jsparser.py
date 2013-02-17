from rpython.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function
from rpython.rlib.parsing.parsing import ParseError
import py
import sys

sys.setrecursionlimit(10000)

GFILE = py.path.local(__file__).dirpath().join('jsgrammar.txt')
try:
    t = GFILE.read(mode='U')
    regexs, rules, ToAST = parse_ebnf(t)
except ParseError, e:
    print e.nice_error_message(filename=str(GFILE), source=t)
    raise

parsef = make_parse_function(regexs, rules, eof=True)


def parse(code):
    t = parsef(code)
    return ToAST().transform(t)
