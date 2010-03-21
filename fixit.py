#!/usr/bin/env python
from re import compile as re
with open("funge.s") as a:a=a.read()
b=re(r"\.L(\d+):\n\tjmp\t\*%rax",8).search(a).groups()[0]
open("funge.s","w").write(a.replace("jmp\t.L"+b,"jmp\t*%rax"))
