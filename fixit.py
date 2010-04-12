#!/usr/bin/env python
from sys import argv
from re import compile as re
with open(argv[1]) as a:a=a.read()
b,c=re(r"\.L(\d+):\n\tjmp\t\*%(...)",8).search(a).groups()[:2]
open(argv[1],"w").write(a.replace("jmp\t.L"+b,"jmp\t*%"+c))
