#!/usr/bin/env python
from sys import argv
with open(argv[1]) as a:a=a.read()
b,c=__import__("re").compile(r"\.L(\d+):\n\tjmp\t\*%(...)",8).search(a).groups()[:2]
open(argv[1],"w").write(a.replace("jmp\t.L"+b,"jmp\t*%"+c))
