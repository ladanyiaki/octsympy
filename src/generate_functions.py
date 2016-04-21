#!/usr/bin/python
"""generate_functions.py

Yo dawg, I heard you like code generation so I wrote a code
generator to write your code generators!
"""

import sys
import os
import sympy as sp

input_list = """exp
log
sqrt|||exp(x)
cbrt
abs|Abs|-1
floor
ceil|ceiling|3/2
sin
sinh
asin
asinh
cos
cosh
acos
acosh
tan
tanh
atan
atanh||1/2
csc
sec
cot
coth
acot
acoth||2
sign
factorial
gamma
erf
erfc
erfinv||1/2
erfcinv
erfi||0,0|
heaviside|Heaviside
dirac|DiracDelta
cosint|Ci|1,0.3374039229009681346626
sinint|Si|1,0.9460830703671830149414
coshint|Chi|1,0.8378669409802082408947
sinhint|Shi|1,1.057250875375728514572
logint|li|2,1.045163780117492784845
"""
# todo:
#psi(x)|polygamma(0,x)
#psi(k,x)|polygamma(k,x)

# sec, csc don't have hyperbolic or arc
#sech asec asech
#csch acsc acsch


copyright_block = \
"""%% Copyright (C) 2015, 2016 Colin B. Macdonald
%%
%% This file is part of OctSymPy.
%%
%% OctSymPy is free software; you can redistribute it and/or modify
%% it under the terms of the GNU General Public License as published
%% by the Free Software Foundation; either version 3 of the License,
%% or (at your option) any later version.
%%
%% This software is distributed in the hope that it will be useful,
%% but WITHOUT ANY WARRANTY; without even the implied warranty
%% of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
%% the GNU General Public License for more details.
%%
%% You should have received a copy of the GNU General Public
%% License along with this software; see the file COPYING.
%% If not, see <http://www.gnu.org/licenses/>.
"""


def process_input_list(L):
    """replace L with a list of dictionaries"""
    LL = L.splitlines();
    L = [];
    for it in LL:
        it = it.split('|')
        #print it
        f = it[0]
        d = {'name':f}
        if len(it) >= 2 and it[1] != '':
            d['spname'] = it[1]
        else:
            d['spname'] = f
        if len(it) >= 3 and it[2] != '':
            testvals = it[2].split(',')
            if len(testvals) == 2:
                (d['test_in_val'],d['test_out_val']) = testvals
                d['out_val_from_oct'] = False
            else:
                (d['test_in_val'],) = testvals
                d['out_val_from_oct'] = True
                d['octname'] = f
        else:
            d['test_in_val'] = '1'
            d['out_val_from_oct'] = True
            d['octname'] = f
        if (len(it) >= 4) and it[3] != '':
            d['docexpr'] = it[3]
        else:
            d['docexpr'] = 'x'
        if (len(it) >= 5):
            d['extra_code'] = it[4]
        else:
            d['extra_code'] = ''
        L.append(d);
    return L



def remove_all(L):
    """FIXME: all a bit hacky, should do better"""
    for d in L:
        f = d['name'];
        fname = '../inst/@sym/%s.m' % f
        try:
            os.unlink(fname)
        except:
            True



def autogen_functions(L, where):
    for d in L:
        f = d['name'];
        fname = '%s/@sym/%s.m' % (where,f)
        print fname

        fd = open(fname, "w")

        fd.write(copyright_block)

        fd.write('\n%% -*- texinfo -*-\n')
        fd.write("%% @documentencoding UTF-8\n")
        fd.write("%%%% @defun %s (@var{x})\n" % f)
        fd.write("%%%% Symbolic %s function.\n" % f)

        # Build and out example block for doctest
        xstr = d['docexpr']
        x = sp.S(xstr)
        y = eval("sp.%s(x)" % d['spname'])
        ystr = sp.pretty(y, use_unicode=True)
        lines = ystr.splitlines()
        if len(lines) > 1:
            # indent multiline output
            lines = [("%%       " + a).strip() for a in lines]
            ystr = "\n" + "\n".join(lines)
        else:
            ystr = " " + ystr
        yutf8 = ystr.encode('utf-8')

        fd.write("%%\n%% Example:\n%% @example\n%% @group\n")
        fd.write("%% syms x\n")
        fd.write("%%%% y = %s(%s)\n" % (f, xstr))
        fd.write("%%%%   @result{} y = (sym)%s\n" % yutf8)
        fd.write("%% @end group\n%% @end example\n")


        fd.write( \
"""%%
%% Note: this file is autogenerated: if you want to edit it, you might
%% want to make changes to 'generate_functions.py' instead.
%%
%% @end defun

%% Author: Colin B. Macdonald
%% Keywords: symbolic

""")

        fd.write("function y = %s(x)\n" % f)
        #fd.write('\n')
        if len(d['extra_code']) > 0:
               fd.write("\n  %s\n\n" % d['extra_code'])
        fd.write("  y = uniop_helper (x, '%s');\n" % d['spname'])
        fd.write("end\n")

        # tests
        fd.write("\n\n%!shared x, d\n")
        fd.write("%%! d = %s;\n" % d['test_in_val'])
        fd.write("%%! x = sym('%s');\n\n" % d['test_in_val'])
        fd.write("%!test\n")
        fd.write("%%! f1 = %s(x);\n" % f)
        if d['out_val_from_oct']:
            fd.write("%%! f2 = %s(d);\n" % f)
        else:
            fd.write("%%! f2 = %s;\n" % d['test_out_val'])
        fd.write("%! assert( abs(double(f1) - f2) < 1e-15 )\n\n")

        fd.write("%!test\n")
        fd.write("%! D = [d d; d d];\n")
        fd.write("%! A = [x x; x x];\n")
        fd.write("%%! f1 = %s(A);\n" % f)
        if d['out_val_from_oct']:
            fd.write("%%! f2 = %s(D);\n" % f)
        else:
            fd.write("%%! f2 = %s;\n" % d['test_out_val'])
            fd.write("%! f2 = [f2 f2; f2 f2];\n")
        fd.write("%! assert( all(all( abs(double(f1) - f2) < 1e-15 )))\n")

        fd.close()


def print_usage():
    print """
  Run this script with one argument:
    python generate_functions install:  make m files in ../inst/@sym
    python generate_functions clean:  remove them from above
"""

if __name__ == "__main__":
    L = process_input_list(input_list)
    print sys.argv
    if len(sys.argv) <= 1:
        print_usage()

    elif sys.argv[1] == 'install':
        print "***** Generating code for .m files from template ****"
        autogen_functions(L, '../inst')
    elif sys.argv[1] == 'clean':
        print "cleaning up"
        remove_all(L)
    else:
        print_usage()


