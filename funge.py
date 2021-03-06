#!/bin/python
def getch():
	try:from termios import tcgetattr,tcsetattr,TCSANOW
	except ImportError:
		from msvcrt import getch
		return lambda:ord(getch())
	from sys import stdin,stdout
	from os import isatty
	def getch():
		stdout.flush()
		fd=stdin.fileno()
		if isatty(fd):
			oldset=tcgetattr(fd)
			newset=oldset[:]
			try:
				newset[3]&=-11
				tcsetattr(fd, TCSANOW, newset)
				return ord(stdin.read(1))
			finally:tcsetattr(fd, TCSANOW, oldset)
		else:
			fd=stdin.read(1)
			return ord(fd) if fd else -1
	return getch
getch = getch()

def main(pro):
	from opcode import opmap,HAVE_ARGUMENT
	from types import CodeType
	from random import getrandbits
	from itertools import repeat
	from sys import stdout
	from collections import defaultdict
	sowrite = stdout.write
	intput=lambda:int(input())
	def mkemit(op):
		op = opmap[op]
		return op.to_bytes(2,"little") if op<HAVE_ARGUMENT else lambda a:(op|a<<8).to_bytes(2,"little") if a<256 else (0x90|a&0xff00|op<<16|(a&0xff)<<24).to_bytes(4,"little")
	swap = mkemit("ROT_TWO")
	rot3 = mkemit("ROT_THREE")
	rot3_2 = rot3 + rot3
	pop = mkemit("POP_TOP")
	dup = mkemit("DUP_TOP")
	iadd = mkemit("INPLACE_ADD")
	add = mkemit("BINARY_ADD")
	subtract = mkemit("BINARY_SUBTRACT")
	multiply = mkemit("BINARY_MULTIPLY")
	floordivide = mkemit("BINARY_FLOOR_DIVIDE")
	modulo = mkemit("BINARY_MODULO")
	lshift = mkemit("BINARY_LSHIFT")
	rshift = mkemit("BINARY_RSHIFT")
	band = mkemit("BINARY_AND")
	subscr = mkemit("BINARY_SUBSCR")
	stscr = mkemit("STORE_SUBSCR")
	unpack2 = mkemit("UNPACK_SEQUENCE")(2)
	tuple2 = mkemit("BUILD_TUPLE")(2)
	giter = mkemit("GET_ITER")
	fiter = mkemit("FOR_ITER")
	lappend1 = mkemit("LIST_APPEND")(1)
	blist1 = mkemit("BUILD_LIST_UNPACK")(1)
	_not = mkemit("UNARY_NOT")
	_neg = mkemit("UNARY_NEGATIVE")
	_pos = mkemit("UNARY_POSITIVE")
	ret = mkemit("RETURN_VALUE")
	cmp = mkemit("COMPARE_OP")
	fmtval = mkemit("FORMAT_VALUE")
	fmtval2 = fmtval(2)
	fmtval4 = fmtval(4)
	cmplt = cmp(0)
	cmpeq = cmp(2)
	cmpgt = cmp(4)
	cmpgte = cmp(5)
	cmpin = cmp(6)
	cmpis = cmp(8)
	call = mkemit("CALL_FUNCTION")
	call0 = call(0)
	call1 = call(1)
	call2 = call(2)
	loadconst = mkemit("LOAD_CONST")
	jumpabs = mkemit("JUMP_ABSOLUTE")
	jumpiforpop = mkemit("JUMP_IF_TRUE_OR_POP")
	jumpif = mkemit("POP_JUMP_IF_TRUE")
	jumpifnot = mkemit("POP_JUMP_IF_FALSE")
	jumpiforpop0 = (0x90|opmap["JUMP_IF_TRUE_OR_POP"]<<16).to_bytes(4,"little")
	jumpif0 = (0x90|opmap["POP_JUMP_IF_TRUE"]<<16).to_bytes(4,"little")
	jumpifnot0 = (0x90|opmap["POP_JUMP_IF_FALSE"]<<16).to_bytes(4,"little")
	addply = add + multiply
	def loadmkconst(c):
		nonlocal constl
		if c in consts:return consts[c]
		else:
			a=consts[c]=loadconst(len(constl))
			constl.append(c)
			return a
	ps = defaultdict(lambda:32)
	X1=Y1=X0=Y0=0
	for Y1,line in enumerate(pro):
		for x,y in enumerate(line):
			if y!=32:ps[x,Y1]=y
		X1=max(X1,x-(y == 10))
	pg={}
	consts={0:b"\x64\2", 1:b"\x64\3", 3:b"\x64\4"}
	pro=set()
	constl=[ps, pro, 0, 1, 3]
	def mvL(x,y):return (X0 if x==X1 else x+1),y
	def mvK(x,y):return x,(Y1 if y==Y0 else y-1)
	def mvH(x,y):return (X1 if x==X0 else x-1),y
	def mvJ(x,y):return x,(Y0 if y==Y1 else y+1)
	def getjoff(off):
		return off+(2 if off<256 else 4)
	class Inst:
		__slots__ = "n", "arg", "var", "sd", "dep", "si"
		def __init__(self, arg):
			self.n = None
			self.arg = arg
			self.var = self.novar
			self.sd = False
			self.dep = 0
			self.si = set()
		def __str__(self, blut={add:"+", subtract:"-", multiply:"*", floordivide:"/", modulo:"%", cmpgt:">", lshift:"<<", rshift:">>", band:"&"}):
			return f"{self.name}\t{blut[self.arg] if self.op is 1 else self.arg}\t{self.var}"
		def isseq(self):return len(self.si) is not 1
		def sguard(self, bc, x):
			dep=self.dep
			if not dep:
				bc += jumpiforpop(getjoff(len(bc) + 4))
				bc += loadmkconst(0)
				bc += loadmkconst(1)
			if x and dep<2:
				bc += dup
				bc += loadmkconst(1)
				bc += cmpeq
				bc += jumpifnot(getjoff(len(bc) + 8))
				bc += loadmkconst(0)
				bc += rot3
				bc += loadmkconst(1)
				bc += add
		def remove(self):
			sn=self.n
			sn.si.remove(self)
			for s in self.si:
				sn.si.add(s)
				if s.n is self:s.n=sn
				if s.arg is self:s.arg=sn
				elif s.op is 12:
					if s.arg[0] is self:s.arg[0]=sn
					if s.arg[1] is self:s.arg[1]=sn
					if s.arg[2] is self:s.arg[2]=sn
	def mkin(op, siop, so, name):
		def f(cls):
			cls.op = op
			cls.siop = siop
			cls.so = so
			cls.name = name
			cls.novar = ((), (None,), (None, None), (None, None, None))[siop]
			cls.new = lambda self:cls(self.arg)
			return cls
		return f
	@mkin(0, 0, 1, "ld")
	class Op0(Inst):
		__slots__ = ()
		def emit(self, bc):
			bc += loadmkconst(self.arg)
		def eval(self, st):
			st.append(self.arg)
			return self.n
	@mkin(1, 2, 1, "bin")
	class Op1(Inst):
		__slots__ = ()
		def emit(self, bc):
			a,b=self.var
			if a is not None:
				if not a and self.arg is subtract:return
				bc += loadmkconst(a)
			elif b is not None:
				if not b and self.arg is subtract:
					bc += _neg
					return
				bc += loadmkconst(b)
				if self.arg not in addply:bc += swap
			bc += self.arg
		def eval(self, st):
			a, b = self.var
			a = a if a is not None else st.pop() if st else 0
			b = b if b is not None else st.pop() if st else 0
			arg = self.arg
			st.append(b+a if arg is add else
				b-a if arg is subtract else
				b*a if arg is multiply else
				b>a if arg is cmpgt else
				b//a if arg is floordivide else
				b%a if arg is modulo else
				b<<a if arg is lshift else
				b>>a if arg is rshift else b&a)
			return self.n
	@mkin(2, 1, 1, "not")
	class Op2(Inst):
		__slots__ = ()
		def emit(self, bc):
			bc += _not
		def eval(self, st):
			a, = self.var
			st.append(not a if a is not None else not st.pop() if st else 1)
			return self.n
	@mkin(3, 1, 0, "pop")
	class Op3(Inst):
		__slots__ = ()
		def emit(self, bc):
			bc += pop
		def eval(self, st):
			if self.var[0] is None and st:st.pop()
			return self.n
	@mkin(4, 1, 2, "dup")
	class Op4(Inst):
		__slots__ = ()
		def emit(self, bc):
			bc += dup
		def eval(self, st):
			a, = self.var
			a = a if a is not None else st.pop() if st else 0
			st.append(a)
			st.append(a)
			return self.n
	@mkin(5, 2, 2, "swp")
	class Op5(Inst):
		__slots__ = ()
		def emit(self, bc):
			a,b=self.var
			if a is b is None:
				bc += swap
			elif a is not None:
				bc += loadmkconst(a)
				bc += swap
			else:
				bc += loadmkconst(b)
		def eval(self, st):
			a, b = self.var
			a = a if a is not None else st.pop() if st else 0
			b = b if b is not None else st.pop() if st else 0
			st.append(a)
			st.append(b)
			return self.n
	@mkin(6, 1, 0, "pr")
	class Op6(Inst):
		__slots__ = ()
		def emit(self, bc):
			a, = self.var
			if a is None:
				if self.arg:
					bc += loadmkconst("c")
					bc += fmtval4
				else:
					bc += _pos
					bc += fmtval2
					bc += loadmkconst(" ")
					bc += add
				bc += loadmkconst(sowrite)
				bc += swap
			else:
				bc += loadmkconst(sowrite)
				bc += loadmkconst(f'{a:c}' if self.arg else f'{+a!r}'+' ')
			bc += call1
			bc += pop
		def eval(self, st):
			a, = self.var
			a = a if a is not None else st.pop() if st else 0
			sowrite(f'{a:c}' if self.arg else f'{+a!r}'+' ')
			return self.n
	@mkin(8, 0, 1, "get")
	class Op8(Inst):
		__slots__ = ()
		def emit(self, bc):
			bc += loadmkconst(self.arg)
			bc += call0
		def eval(self, st):
			st.append(self.arg())
			return self.n
	emit10h = tuple2 + loadconst(0) + swap + subscr
	@mkin(10, 2, 1, "rem")
	class Op10(Inst):
		__slots__ = ()
		def emit(self, bc):
			a,b = self.var
			if a is b is None:
				bc += emit10h
			elif a is not None and b is not None:
				bc += loadconst(0)
				bc += loadmkconst((b,a))
				bc += subscr
			elif a is not None:
				bc += loadmkconst(a)
				bc += emit10h
			else:
				bc += loadmkconst(b)
				bc += swap
				bc += emit10h
		def eval(self, st):
			a, b = self.var
			a = a if a is not None else st.pop() if st else 0
			b = b if b is not None else st.pop() if st else 0
			st.append(ps[b,a])
			return self.n
	ret11pos = None
	def emit11ret(bc):
		nonlocal ret11pos
		if ret11pos is None:
			ret11pos = len(bc)
			bc += blist1
			bc += swap
			bc += loadmkconst(repeat)
			bc += swap
			bc += dup
			bc += call2
			bc += giter
			j1 = jumpabs(len(bc))
			bc += fiter(10 + len(j1))
			bc += pop
			bc += rot3
			bc += swap
			bc += lappend1
			bc += swap
			bc += j1
			bc += ret
		else:bc += jumpabs(ret11pos)
		return ...
	@mkin(11, 3, 0, "wem")
	class Op11(Inst):
		__slots__ = ()
		def isseq(self):return len(ir.si) is not 1 or self.var[0] is None or self.var[1] is None or (self.var[1],self.var[0]) in pro
		def emit(self, bc):
			a,b,c=self.var
			if a is b is None:
				if c is None:
					self.sguard(bc, True)
					bc += dup
					bc += loadmkconst(2)
					bc += cmpis
					bc += jumpifnot(getjoff(len(bc) + 6))
					bc += _not
					bc += rot3
					bc += loadmkconst(3)
					bc += loadmkconst(3)
					bc += subtract
					bc += rot3
					bc += tuple2
					bc += swap
					bc += rot3
					bc += dup
					bc += rot3
				else:
					self.sguard(bc, True)
					bc += loadmkconst(2)
					bc += subtract
					bc += rot3
					bc += tuple2
					bc += dup
					bc += loadmkconst(c)
					bc += swap
				bc += loadconst(0)
				bc += swap
				bc += stscr
				bc += loadconst(1)
				bc += cmpin
				j4 = len(bc)+1
				bc += jumpifnot0
				bc += loadmkconst(self.arg)
				emit11ret(bc)
				bc[j4+2],bc[j4]=len(bc).to_bytes(2,"little")
			elif a is not None and b is not None:
				a=b,a
				if c is not None:bc += loadmkconst(c)
				elif a in pro or len(ir.si) is not 1:
					self.sguard(bc, False)
					bc += loadmkconst(1)
					bc += subtract
					bc += swap
				bc += loadconst(0)
				bc += loadmkconst(a)
				bc += stscr
				if a in pro:
					bc += loadmkconst(self.arg)
					return emit11ret(bc)
			else:
				if c is not None:
					self.sguard(bc, False)
					bc += loadmkconst(1)
				else:
					self.sguard(bc, True)
					bc += loadmkconst(2)
				bc += subtract
				bc += rot3 if c is None else swap
				if b is None:
					bc += loadmkconst(a)
				else:
					bc += loadmkconst(b)
					bc += swap
				bc += tuple2
				bc += dup
				if c is not None:
					bc += loadmkconst(c)
					bc += swap
				else:bc += rot3
				bc += loadconst(0)
				bc += swap
				bc += stscr
				bc += loadconst(1)
				bc += cmpin
				j4 = len(bc)+1
				bc += jumpifnot0
				bc += loadmkconst(self.arg)
				emit11ret(bc)
				bc[j4+2],bc[j4]=len(bc).to_bytes(2,"little")
		def eval(self, st):
			a, b, c = self.var
			a = a if a is not None else st.pop() if st else 0
			b = b if b is not None else st.pop() if st else 0
			c = c if c is not None else st.pop() if st else 0
			a=b,a
			ps[a]=c
			return [*self.arg,*reversed(st)] if a in pro else self.n
	@mkin(12, 0, 0, "jr")
	class Op12(Inst):
		__slots__ = ()
		def isseq(self):return True
		def emit(self, bc):
			bc += loadmkconst(getrandbits)
			bc += loadmkconst(2)
			bc += call1
			bc += dup
			j1 = len(bc)+1
			bc += jumpifnot0
			bc += dup
			bc += loadmkconst(1)
			bc += cmpis
			j2 = len(bc)+1
			bc += jumpif0
			bc += dup
			bc += loadmkconst(2)
			bc += cmpis
			j3 = len(bc)+1
			bc += jumpif0
			self.arg.sort(key=lambda x:x.sd is not True)
			if self.arg[0].sd is not True and bc[self.arg[0].sd-2] is 1:
				bc += jumpabs(self.arg[0].sd-2)
			else:
				bc += pop
				compile2(self.arg[0], bc)
			if self.arg[1].sd is not True and bc[self.arg[1].sd-2] is 1:
				bc[j1+2],bc[j1]=(self.arg[1].sd-2).to_bytes(2,"little")
			else:
				bc[j1+2],bc[j1]=len(bc).to_bytes(2,"little")
				bc += pop
				compile2(self.arg[1], bc)
			if self.arg[2].sd is not True and bc[self.arg[2].sd-2] is 1:
				bc[j2+2],bc[j2]=(self.arg[2].sd-2).to_bytes(2,"little")
			else:
				bc[j2+2],bc[j2]=len(bc).to_bytes(2,"little")
				bc += pop
				compile2(self.arg[2], bc)
			if self.n.sd is not True and bc[self.n.sd-2] is 1:
				bc[j3+2],bc[j3]=(self.n.sd-2).to_bytes(2,"little")
				return ...
			else:
				bc[j3+2],bc[j3]=len(bc).to_bytes(2,"little")
				bc += pop
		def eval(self, st):
			st=getrandbits(2)
			return self.n if st is 3 else self.arg[st]
	@mkin(13, 1, 0, "jz")
	class Op13(Inst):
		__slots__ = ()
		def isseq(self):return True
		def emit(self, bc):
			self.sguard(bc, False)
			bc += loadmkconst(1)
			bc += subtract
			bc += swap
			if self.arg.sd is True:
				j2 = len(bc)+1
				bc += jumpif0
				compile2(self.arg, bc)
				bc[j2+2],bc[j2]=len(bc).to_bytes(2,"little")
			else:
				bc += jumpifnot(self.arg.sd)
		def eval(self, st):
			a, = self.var
			return self.n if (a if a is not None else (st and st.pop())) else self.arg
	@mkin(14, 0, 0, "ret")
	class Op14(Inst):
		__slots__ = ()
		def emit(self, bc):
			bc += loadmkconst(None)
			bc += ret
			return ...
		def eval(self, st):return
	@mkin(16, 0, 0, "nop")
	class Op16(Inst):
		__slots__ = ()
		def emit(self, bc):return
		def eval(self, st):return self.n
	def compile(i,mv,
		bins={37:modulo,42:multiply,43:add,45:subtract,47:floordivide,96:cmpgt},
		raw={33:Op2,36:Op3,58:Op4,92:Op5,103:Op10},
		mvs={60:mvH,62:mvL,94:mvK,118:mvJ},
		ops={64:10,34:9,35:11,38:3,44:1,126:2,46:0,112:5,124:7,95:8,63:6}
	):
		def emit(op, arg=None):
			nonlocal inst
			pist.clear()
			tail=inst
			inst=Op16(None)
			tail.__class__=op
			tail.n=inst
			tail.arg=arg
			tail.var=tail.novar
			inst.si.add(tail)
			return tail
		head=inst=Op16(None)
		pist=[]
		while True:
			i=mv(*i)
			imv=i,mv
			if imv in pg:
				i2=pg[imv]
				if inst is not i2:
					for i in pist:pg[i]=i2
					if inst is head:return i2
					for i in inst.si:
						i.n=i2
						i2.si.add(i)
				else:inst.n=inst
				return head
			pg[imv]=inst
			pist.append(imv)
			pro.add(i)
			i2 = ps[i]
			if 48<=i2<58:emit(Op0, i2-48)
			elif i2 in mvs:mv=mvs[i2]
			elif i2 in bins:emit(Op1, bins[i2])
			elif i2 in raw:emit(raw[i2])
			elif i2 in ops:
				i2=ops[i2]
				if i2>8:
					if i2 is 11:i=mv(*i)
					elif i2 is 9:
						while True:
							i=mv(*i)
							pro.add(i)
							i2=ps[i]
							if i2 is 34:break
							emit(Op0, i2)
					elif i2 is 10:
						node14 = emit(Op14)
						node14.n = None
						node14.sd = True
						return head
				elif i2<4:
					if i2<2:emit(Op6, i2)
					else:emit(Op8, (intput if i2 is 3 else getch))
				elif i2>6:
					if i2 is 7:
						i2=mvJ
						mv=mvK
					else:
						i2=mvL
						mv=mvH
					i2=emit(Op13, compile(i,i2))
					i2.arg.si.add(i2)
				elif i2 is 5:emit(Op11, imv)
				elif i2 is 6:
					i2=emit(Op12, [compile(i,mvL), compile(i,mvK), compile(i,mvH)])
					for mv in i2.arg:mv.si.add(i2)
					mv=mvJ
	def calcvar(lir, cst):
		if not cst:return
		ir=lir.n
		if ir.sd:return
		while ir.op is 16:
			if lir is ir:return
			ir.si.remove(lir)
			ir=lir.n=ir.n
			ir.si.add(lir)
		if not ir.var:
			ir.dep=len(cst)
			return
		op=ir.op
		if op is 13:
			if cst[-1] is not None:
				c0=cst.pop()
				c0.__class__=Op16
				c0.var=()
				lir.n = ir.n if c0.arg else ir.arg
				if lir.n is ir:return
				lir.n.si.add(lir)
				ir.si.remove(lir)
				if not ir.si:
					ir.n.si.remove(ir)
					ir.arg.si.remove(ir)
				return calcvar(lir, cst)
			elif len(ir.si) is 1:
				ir.dep=len(cst)
				if lir.op is 2:
					lir.__class__=Op16
					lir.var=()
					ir.dep=len(cst)
					ir.n,ir.arg=ir.arg,ir.n
			return
		elif op is 4:
			if ir.n.op in (3,5):
				a=ir.n.op
				ir.n.si.remove(ir)
				ir.n=ir.n.n
				ir.n.si.add(ir)
				if a is 3:
					ir.remove()
					return calcvar(lir, cst)
			else:
				b=cst[-1]
				if b is not None:
					if len(ir.si) is 1:
						ir.__class__=Op0
						ir.arg=b.arg
						ir.var=()
					else:
						ir.si.remove(lir)
						a=ir.n
						lir.n=ir=Op0(b.arg)
						ir.si.add(lir)
						ir.n=a
						return a.si.add(ir)
				elif len(ir.si) is 1:ir.dep=len(cst)
				return
		elif op is 5 and cst[-1] is not None and len(cst)>1 and cst[-2] is not None:
			cst[-1].arg,cst[-2].arg=cst[-2].arg,cst[-1].arg
			lir.n=ir.n
			if lir.n is ir:return
			lir.n.si.add(lir)
			ir.si.remove(lir)
			if not ir.si:ir.n.si.remove(ir)
			return calcvar(lir, cst)
		if len(ir.si) is not 1:
			if any(cst[-ir.siop:]):
				ir.si.remove(lir)
				if not ir.si:ir.n.si.remove(ir)
				a=ir.n
				lir.n=ir=ir.new()
				ir.si.add(lir)
				ir.n=a
				a.si.add(ir)
				return calcvar(lir, cst)
		else:
			def calcvarhelper():
				b=len(cst)
				a=min(ir.siop, b)
				c=-a
				x=-1
				while x>=c:
					c0=cst[x]
					if c0 is not None:
						del cst[x]
						c0.__class__ = Op16
						c0.var=()
						c+=1
						yield c0.arg
					else:
						x-=1
						yield None
				if b is a:yield from repeat(None, ir.siop-b)
			ir.var=(*calcvarhelper(),)
			ir.dep=len(cst)
			if op<5:
				if op is 1:
					a,b = ir.var
					c = ir.arg
					if a is not None:
						if b is not None:
							ir.__class__=Op0
							ir.arg=(b+a if c is add else
								b-a if c is subtract else
								b*a if c is multiply else
								b>a if c is cmpgt else
								0 if not a else
								b//a if c is floordivide else b%a)
							ir.var=()
						elif not a:
							if c is add or c is subtract:
								ir.__class__ = Op16
								ir.arg = None
								ir.var = ()
							elif c is multiply:
								ir.__class__ = Op3
								ir.arg = None
								ir.var = None,
								a = Op0()
								a.arg = 0
								a.n = ir.n
								ir.n = a
								a.n.si.remove(ir)
								a.n.si.add(a)
								a.si.add(ir)
						elif a>0 and not a&(a-1):
							if c is modulo:
								ir.var = a-1, None
								ir.arg = band
							elif c is floordivide:
								ir.var = a.bit_length()-1, None
								ir.arg = rshift
							elif c is multiply:
								ir.var = a.bit_length()-1, None
								ir.arg = lshift
				elif None not in ir.var:
					if op is 4:
						c,=ir.var
						ir.__class__=Op0
						ir.arg=c
						ir.var=()
						a=ir.n
						b=ir.n=Op0(c)
						b.si.add(ir)
						b.n=a
						a.si.remove(ir)
						return a.si.add(b)
					elif op is 3:
						ir.remove()
						return calcvar(lir, cst)
					elif op is 2:
						ir.__class__=Op0
						a,=ir.var
						a=ir.arg=not a
						ir.var=()
	def nohole(ir):
		while not ir.sd:
			ir.sd=True
			if ir.op is 13:nohole(ir.arg)
			elif ir.op is 12:
				for a in ir.arg:nohole(a)
			ir=ir.n
	def peephole(ir):
		cst=[]
		while True:
			while True:
				if ir.sd:return
				op=ir.op
				if not op:
					if len(ir.si) is not 1:cst.clear()
					cst.append(ir)
					break
				elif op is 13:
					if ir.n is ir.arg:
						op=3
						ir.__class__=Op3
						ir.arg=None
					else:
						ir.sd=True
						peephole(ir.arg)
						ir=ir.n
						cst.clear()
						continue
				elif op is 12:
					ir.sd=True
					for a in ir.arg:peephole(a)
					ir=ir.n
					cst.clear()
					continue
				elif op is 11:
					a,b,c=ir.var
					if a is not None and b is not None:
						if (b,a) in pro:
							ir.sd=True
							ir.n.si.remove(ir)
							a=ir.n
							while not a.si:
								b=a.n
								if b:b.si.remove(a)
								else:break
								a=b
							ir.n=None
							return
					else:cst.clear()
					calcvar(ir, cst)
					ir.sd=True
					ir=ir.n
					continue
				if len(ir.si) is not 1:
					ir.dep=0
					cst.clear()
					cst += repeat(None, ir.so)
				else:
					a=ir.var.count(None)
					if a:cst[-a:]=repeat(None, ir.so)
					elif ir.so:cst+=repeat(None, ir.so)
				break
			calcvar(ir, cst)
			ir.sd=True
			ir=ir.n
	def execir(ir):
		st=[]
		try:
			while True:ir=ir.eval(st)
		except AttributeError:return ir
	def compile2pre(ir, bc):
		st = []
		while not ir.isseq():
			ir=ir.eval(st)
			if not ir:
				bc += loadmkconst(None)
				bc += ret
				return
		for dep in map(loadmkconst, st):
			bc += dep
		dep = len(st)
		bc += loadmkconst(dep)
		ir.dep = dep
		return compile2(ir, bc)
	def compile2(ir, bc):
		adj=dep=0
		while ir.sd is True:
			siop=ir.var.count(None)
			odep = dep
			dep += ir.so-siop
			ir.dep = max(min(i.dep-i.var.count(None)+i.so for i in ir.si), 0)
			seq = ir.isseq()
			if seq or dep>2 or odep<siop or ir.dep<siop:
				dep=ir.so
				if odep is 1:bc += swap
				elif odep is 2:bc += rot3_2
				if not seq and ir.dep>=siop:
					adj+=siop-odep
				else:
					if odep != adj:
						bc += loadmkconst(odep-adj)
						bc += add
					if seq:
						seq=11<=ir.op<=13
						adj=not seq and siop
					else:
						adj=siop
				ir.sd=len(bc)
				if siop and not seq:
					ir.sguard(bc, siop is 2)
					if siop is 1:bc += swap
					else:bc += rot3
			if ir.emit(bc) is ...:return
			ir=ir.n
		if dep is 1:bc += swap
		elif dep is 2:bc += rot3_2
		if dep != adj:
			bc += loadmkconst(dep-adj)
			bc += add
		bc += jumpabs(ir.sd)
	bc=bytearray()
	root=Op16(None)
	ir=compile((X1,0),mvL)
	while True:
		pg.clear()
		root.n=ir
		ir.si.add(root)
		peephole(ir)
		compile2pre(ir, bc)
		f=eval(CodeType(0,0,0,65536,0,bytes(bc),tuple(constl),(),(),"","",0,b""))
		if not f:return
		f=iter(f)
		ret11pos = None
		bc.clear()
		pro.clear()
		for x,y in ps.keys():
			if x<X0:X0=x
			elif x>X1:X1=x
			if y<Y0:Y0=y
			elif y>Y1:Y1=y
		ir=tail=compile(next(f), next(f))
		for ir in map(Op0,f):
			ir.n=tail
			tail.si.add(ir)
			tail=ir
if __name__ == "__main__":
	from sys import argv
	main(open(argv[1],"rb"))
