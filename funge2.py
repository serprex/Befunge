#!/bin/python
def getch():
	try:from termios import tcgetattr,tcsetattr,TCSANOW
	except ImportError:
		from msvcrt import getch
		return lambda:ord(getch())
	from sys import stdin,stdout
	def getch():
		stdout.flush()
		fd=stdin.fileno()
		oldset=tcgetattr(fd)
		newset=oldset[:]
		try:
			newset[3]&=-11
			tcsetattr(fd, TCSANOW, newset)
			return ord(stdin.read(1))
		finally:tcsetattr(fd, TCSANOW, oldset)
	return getch
getch = getch()

def main(pro):
	from opcode import opmap,HAVE_ARGUMENT
	from types import CodeType,FunctionType
	from random import getrandbits
	from itertools import repeat
	from sys import stdout
	from collections import defaultdict
	sowrite = stdout.write
	intput=lambda:int(input())
	def mkemit(op):
		op = opmap[op]
		return op.to_bytes(1,"little") if op<HAVE_ARGUMENT else lambda a:(op|a<<8).to_bytes(3,"little")
	swap = mkemit("ROT_TWO")
	rot3 = mkemit("ROT_THREE")
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
	ret = mkemit("RETURN_VALUE")
	cmp = mkemit("COMPARE_OP")
	cmplt = cmp(0)
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
	jump = b"q\0\0"
	jumpiforpop = opmap["JUMP_IF_TRUE_OR_POP"].to_bytes(3,"little")
	jumpifnotorpop = opmap["JUMP_IF_FALSE_OR_POP"].to_bytes(3,"little")
	jumpif = opmap["POP_JUMP_IF_TRUE"].to_bytes(3,"little")
	jumpifnot = opmap["POP_JUMP_IF_FALSE"].to_bytes(3,"little")
	addply = add + multiply
	def loadmkconst(c):
		nonlocal constl
		if c in consts:return consts[c]
		else:
			a=consts[c]=(100|len(constl)<<8).to_bytes(3,"little")
			constl.append(c)
			return a
	ps = defaultdict(lambda:32)
	X1=Y1=X0=Y0=0
	for Y1,line in enumerate(pro):
		for x,c in enumerate(line):
			if c!=32:ps[x,Y1]=c
		X1=max(X1,x)
	WID=X1+1
	HEI=Y1+1
	pg={}
	consts={}
	pro=set()
	constl=[ps, pro]
	def mvL(x,y):
		x+=1
		return (x-WID if x>X1 else x),y
	def mvK(x,y):
		y-=1
		return x,(y+HEI if y<Y0 else y)
	def mvH(x,y):
		x-=1
		return (x+WID if x<X0 else x),y
	def mvJ(x,y):
		y+=1
		return x,(y-HEI if y>Y1 else y)
	bins = add, subtract, multiply, floordivide, modulo, cmpgt
	class Inst:
		__slots__ = "n", "arg", "var", "sd", "dep", "si"
		def __init__(self, arg):
			self.n = None
			self.arg = arg
			self.var = self.novar
			self.sd = False
			self.dep = 0
			self.si = set()
		def __str__(self, blut= {add:"+", subtract:"-", multiply:"*", floordivide:"/", modulo:"%", cmpgt:">"}):
			return "%s\t%s\t%s"%(self.name,blut[self.arg] if self.op is 1 else self.arg,self.var)
		def eval(self, st):return self.eva(st, *((c if c is not None else st.pop() if st else 0) for c in self.var))
		def sguard(self, bc, x):
			dep=self.dep
			if dep<=x:
				if not x:
					j1=len(bc)+1
					bc += jumpiforpop
					bc += loadmkconst(0)
					bc += loadmkconst(1)
					bc[j1],bc[j1+1]=len(bc).to_bytes(2,"little")
				elif x is dep:
					bc += dup
					bc += loadmkconst(x)
					bc += cmpgt
					j1=len(bc)+1
					bc += jumpif
					bc += _not
					bc += loadmkconst(x+1)
					bc[j1],bc[j1+1]=len(bc).to_bytes(2,"little")
				else:
					j1=len(bc)+1
					bc += jump
					bc += loadmkconst(1)
					bc += add
					bc += loadmkconst(0)
					bc += swap
					bc[j1],bc[j1+1]=len(bc).to_bytes(2,"little")
					bc += dup
					bc += loadmkconst(x)
					bc += cmpgt
					bc += jumpifnot
					bc[-2:]=(j1+2).to_bytes(2,"little")
		def remove(self):
			sn=self.n
			sn.si.remove(self)
			for s in self.si:
				sn.si.add(s)
				if s.n is self:s.n=sn
				if s.arg is self:s.arg=sn
				elif s.op is 12:
					for sa in 0,1,2:
						if s.arg[sa] is self:s.arg[sa]=sn
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
			bc += loadmkconst(1)
			bc += add
			bc += loadmkconst(self.arg)
			bc += swap
		def eva(self, st):
			st.append(self.arg)
			return self.n
	@mkin(1, 2, 1, "bin")
	class Op1(Inst):
		__slots__ = ()
		def emit(self, bc):
			a,b=self.var
			if a is b is None:
				self.sguard(bc, 1)
				bc += loadmkconst(-1)
				bc += add
				bc += rot3
				bc += self.arg
				bc += swap
			else:
				if a is not None:
					self.sguard(bc, 0)
					if not a and self.arg is subtract:
						bc += _neg
						bc += swap
						return
					bc += swap
					bc += loadmkconst(a)
				else:
					bc += swap
					bc += loadmkconst(b)
					if self.arg not in addply:bc += swap
				bc += self.arg
				bc += swap
		def eva(self, st, a, b):
			arg = self.arg
			st.append(b+a if arg is add else
				b-a if arg is subtract else
				b*a if arg is multiply else
				b>a if arg is cmpgt else
				b//a if arg is floordivide else b%a)
			return self.n
	@mkin(2, 1, 1, "not")
	class Op2(Inst):
		__slots__ = ()
		def emit(self, bc):
			self.sguard(bc, 0)
			bc += swap
			bc += _not
			bc += swap
		def eva(self, st, a):
			st.append(not a)
			return self.n
	@mkin(3, 1, 0, "pop")
	class Op3(Inst):
		__slots__ = ()
		def emit(self, bc):
			if not self.dep:
				bc += dup
				jt = len(bc)+1
				bc += jumpifnot
			bc += loadmkconst(-1)
			bc += add
			bc += swap
			bc += pop
			if not self.dep:bc[jt],bc[jt+1]=len(bc).to_bytes(2,"little")
		def eva(self, st, a):return self.n
	@mkin(4, 1, 2, "dup")
	class Op4(Inst):
		__slots__ = ()
		def emit(self, bc):
			self.sguard(bc, 0)
			bc += loadmkconst(1)
			bc += add
			bc += swap
			bc += dup
			bc += rot3
			bc += swap
		def eva(self, st, a):
			st.append(a)
			st.append(a)
			return self.n
	@mkin(5, 2, 2, "swp")
	class Op5(Inst):
		__slots__ = ()
		def emit(self, bc):
			a,b=self.var
			if a is b is None:
				self.sguard(bc, 1)
				bc += rot3
				bc += swap
				bc += rot3
				bc += rot3
			elif a is not None:
				self.sguard(bc, 0)
				bc += loadmkconst(1)
				bc += add
				bc += loadmkconst(a)
				bc += rot3
			else:
				bc += loadmkconst(1)
				bc += add
				bc += loadmkconst(b)
				bc += swap
		def eva(self, st, a, b):
			st.append(a)
			st.append(b)
			return self.n
	@mkin(6, 1, 0, "pr")
	class Op6(Inst):
		__slots__ = ()
		def emit(self, bc):
			a, = self.var
			if a is None:
				self.sguard(bc, 0)
				bc += loadmkconst(-1)
				bc += add
				bc += swap
				bc += loadmkconst(self.arg)
				bc += swap
				bc += modulo
				bc += loadmkconst(sowrite)
				bc += swap
			else:
				bc += loadmkconst(sowrite)
				bc += loadmkconst(self.arg%a)
			bc += call1
			bc += pop
		def eva(self, st, a):
			sowrite(self.arg%a)
			return self.n
	@mkin(8, 0, 1, "get")
	class Op8(Inst):
		__slots__ = ()
		def emit(self, bc):
			bc += loadmkconst(1)
			bc += add
			bc += loadmkconst(self.arg)
			bc += call0
			bc += swap
		def eva(self, st):
			st.append(self.arg())
			return self.n
	emit10h = tuple2 + loadconst(0) + swap + subscr + swap
	@mkin(10, 2, 1, "rem")
	class Op10(Inst):
		__slots__ = ()
		def emit(self, bc):
			a,b = self.var
			if a is b is None:
				self.sguard(bc, 1)
				bc += loadmkconst(-1)
				bc += add
				bc += rot3
				bc += emit10h
			elif a is not None and b is not None:
				bc += loadmkconst(1)
				bc += add
				bc += loadconst(0)
				bc += loadmkconst((b,a))
				bc += subscr
				bc += swap
			elif a is not None:
				self.sguard(bc, 0)
				bc += swap
				bc += loadmkconst(a)
				bc += emit10h
			else:
				bc += swap
				bc += loadmkconst(b)
				bc += swap
				bc += emit10h
		def eva(self, st, a, b):
			a=b,a
			st.append(ps[a])
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
			j1 = (ret11pos+13).to_bytes(2,"little")
			bc += fiter(10)
			bc += pop
			bc += rot3
			bc += swap
			bc += lappend1
			bc += swap
			bc += jump
			bc[-2:]=j1
			bc += ret
		else:bc += jumpabs(ret11pos)
		return ...
	@mkin(11, 3, 0, "wem")
	class Op11(Inst):
		__slots__ = ()
		def emit(self, bc):
			a,b,c=self.var
			if a is b is None:
				if c is None:
					self.sguard(bc, 2)
					bc += loadmkconst(-3)
				else:
					self.sguard(bc, 1)
					bc += loadmkconst(-2)
				bc += add
				bc += rot3
				bc += tuple2
				if c is None:
					bc += swap
					bc += rot3
					bc += dup
					bc += rot3
				else:
					bc += dup
					bc += loadmkconst(c)
					bc += swap
				bc += loadconst(0)
				bc += swap
				bc += stscr
				bc += loadconst(1)
				bc += cmpin
				j4 = len(bc)+1
				bc += jumpifnot
				bc += loadmkconst(self.arg)
				emit11ret(bc)
				bc[j4],bc[j4+1]=len(bc).to_bytes(2,"little")
			elif a is not None and b is not None:
				a=b,a
				if c is not None:
					bc += loadmkconst(c)
				else:
					self.sguard(bc, 0)
					bc += loadmkconst(-1)
					bc += add
					bc += swap
				bc += loadconst(0)
				bc += loadmkconst(a)
				bc += stscr
				if a in pro:
					bc += loadmkconst(self.arg)
					return emit11ret(bc)
			else:
				if c is not None:
					self.sguard(bc, 0)
					bc += loadmkconst(-1)
				else:
					self.sguard(bc, 1)
					bc += loadmkconst(-2)
				bc += add
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
				bc += jumpifnot
				bc += loadmkconst(self.arg)
				emit11ret(bc)
				bc[j4],bc[j4+1]=len(bc).to_bytes(2,"little")
		def eva(self, st, a, b, c):
			a=b,a
			ps[a]=c
			if a in pro:
				pro.clear()
				return [*self.arg,*reversed(st)]
			return self.n
	@mkin(12, 0, 0, "jr")
	class Op12(Inst):
		__slots__ = ()
		def emit(self, bc):
			bc += loadmkconst(getrandbits)
			bc += loadmkconst(2)
			bc += call1
			bc += dup
			j1 = len(bc)+1
			bc += jumpifnot
			bc += dup
			bc += loadmkconst(1)
			bc += cmpis
			j2 = len(bc)+1
			bc += jumpif
			bc += dup
			bc += loadmkconst(2)
			bc += cmpis
			j3 = len(bc)+1
			bc += jumpif
			self.arg.sort(lambda x:x.sd is not True)
			if self.arg[0].sd is not True and bc[self.arg[0].sd-1] is 1:
				bc += jumpabs(self.arg[0].sd-1)
			else:
				bc += pop
				compile2(self.arg[0], bc)
			if self.arg[1].sd is not True and bc[self.arg[1].sd-1] is 1:
				bc[j1],bc[j1+1]=(self.arg[1].sd-1).to_bytes(2,"little")
			else:
				bc[j1],bc[j1+1]=len(bc).to_bytes(2,"little")
				bc += pop
				compile2(self.arg[1], bc)
			if self.arg[2].sd is not True and bc[self.arg[2].sd-1] is 1:
				bc[j2],bc[j2+1]=(self.arg[2].sd-1).to_bytes(2,"little")
			else:
				bc[j2],bc[j2+1]=len(bc).to_bytes(2,"little")
				bc += pop
				compile2(self.arg[2], bc)
			if self.n.sd is not True and bc[self.n.sd-1] is 1:
				bc[j3],bc[j3+1]=(self.n.sd-1).to_bytes(2,"little")
				return ...
			else:
				bc[j3],bc[j3+1]=len(bc).to_bytes(2,"little")
				bc += pop
		def eva(self, st):
			c=getrandbits(2)
			return self.n if c is 3 else self.arg[c]
	@mkin(13, 1, 0, "jz")
	class Op13(Inst):
		__slots__ = ()
		def emit(self, bc):
			j1 = len(bc)+1
			bc += jumpiforpop
			bc += loadmkconst(0)
			j3 = len(bc)+1
			bc += jump
			bc[j1],bc[j1+1]=len(bc).to_bytes(2,"little")
			bc += loadmkconst(-1)
			bc += add
			bc += swap
			if self.arg.sd is True:
				j2 = len(bc)+1
				bc += jumpif
				bc[j3],bc[j3+1]=len(bc).to_bytes(2,"little")
				compile2(self.arg, bc)
				bc[j2],bc[j2+1]=len(bc).to_bytes(2,"little")
			else:
				bc += jumpifnot
				bc[-2:]=bc[j3],bc[j3+1]=self.arg.sd.to_bytes(2,"little")
		def eva(self, st, a):return self.n if a else self.arg
	@mkin(14, 0, 0, "ret")
	class Op14(Inst):
		__slots__ = ()
		def emit(self, bc):
			bc += loadmkconst(None)
			bc += ret
			return ...
		def eva(self, st):return
	@mkin(16, 0, 0, "nop")
	class Op16(Inst):
		__slots__ = ()
		def emit(self, bc):return
		def eva(self, st):return self.n
	def compile(i,mv):
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
			if 33<=i2<=126:
				i2=b'\x10\x1d\x1f\x11\x0e\x17$$$\x0c\n\x15\x0b\x14\r\0\1\2\3\4\5\6\7\x08\t\x12$"$ \x1a\x1e$$$$$$$$$$$$$$$$$$$$$$$$$$$\x13$!\x1c\x0f$$$$$$\x18$$$$$$$$\x19$$$$$#$$$$$\x1b$\x16'[i2-33]
				if i2<10:emit(Op0, i2)
				elif i2<16:emit(Op1, bins[i2-10])
				elif i2>28:
					if i2 is 31:i=mv(*i)
					elif i2 is 36:continue
					elif i2>31:mv = mvL if i2 is 32 else mvK if i2 is 33 else mvH if i2 is 34 else mvJ
					elif i2 is 29:
						while True:
							i=mv(*i)
							pro.add(i)
							i2=ps[i]
							if i2 is 34:break
							emit(Op0, i2)
					elif i2 is 30:
						for i in pist:pg[i]=node14
						if inst is head:return node14
						for i in inst.si:
							i.n=node14
							node14.si.add(i)
						return head
				elif i2<24:
					if i2<20:emit(Op2 if i2 is 16 else Op3 if i2 is 17 else Op4 if i2 is 18 else Op5)
					elif i2<22:emit(Op6, ("%c" if i2 is 21 else "%d "))
					else:emit(Op8, (intput if i2 is 23 else getch))
				elif i2>26:
					if i2 is 27:
						i2=mvJ
						mv=mvK
					else:
						i2=mvL
						mv=mvH
					i2=emit(Op13, compile(i,i2))
					i2.arg.si.add(i2)
				elif i2 is 24:emit(Op10)
				elif i2 is 25:emit(Op11, imv)
				elif i2 is 26:
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
			if cst[-1][1] is not None:
				c0,c1=cst.pop()
				c0.__class__=Op16
				c0.var=()
				lir.n = ir.n if c1 else ir.arg
				lir.n.si.add(lir)
				ir.si.remove(lir)
				if not ir.si:
					ir.n.si.remove(ir)
					ir.arg.si.remove(ir)
				return calcvar(lir, cst)
			elif len(ir.si) is 1:ir.dep=len(cst)
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
				b=cst[-1][1]
				if b is not None:
					if len(ir.si) is 1:
						ir.__class__=Op0
						ir.arg=b
						ir.var=()
					else:
						ir.si.remove(lir)
						a=ir.n
						lir.n=ir=Op0(b)
						ir.si.add(lir)
						ir.n=a
						a.si.add(ir)
						return
				elif len(ir.si) is 1:ir.dep=len(cst)
				return
		if len(ir.si) is not 1:
			if any(a is not None for a,a in cst[-ir.siop:]):
				ir.si.remove(lir)
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
					c0,c1=cst[x]
					yield c1
					if c1 is not None:
						del cst[x]
						c0.__class__ = Op16
						c0.var=()
						c+=1
					else:x-=1
				if b is a:yield from repeat(None, ir.siop-b)
			ir.var=(*calcvarhelper(),)
			ir.dep=len(cst)
			if op<6:
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
						elif not a&(a-1) and a:
							if c is modulo:
								ir.var = a-1, None
								ir.arg = band
							elif c is floordivide:
								ir.var = a.bit_length()-1, None
								ir.arg = rshift
							elif c is multiply:
								ir.var = a.bit_length()-1, None
								ir.arg = lshift
				elif op is 3:
					ir.remove()
					return calcvar(lir, cst)
				elif op is 4:
					c,=ir.var
					ir.__class__=Op0
					ir.arg=c
					ir.var=()
					a=ir.n
					b=ir.n=Op0(c)
					b.si.add(ir)
					b.n=a
					a.si.remove(ir)
					a.si.add(b)
				elif op is 2:
					ir.__class__=Op0
					a,=ir.var
					a=ir.arg=not a
					ir.var=()
				else:
					c,op=ir.var
					ir.sd=True
					ir.__class__=Op0
					ir.arg=c
					ir.var=()
					a=ir.n
					b=ir.n=Op0(op)
					b.si.add(ir)
					b.n=a
					a.si.remove(ir)
					a.si.add(b)
	def weakhole(ir):
		while not ir.sd:
			ir.sd=True
			if ir.op is 13:weakhole(ir.arg)
			elif ir.op is 12:
				for a in ir.arg:weakhole(a)
			ir=ir.n
	def peephole(ir):
		cst=[]
		while True:
			while True:
				if ir.sd:return
				op=ir.op
				if not op:
					if len(ir.si) is not 1:cst.clear()
					cst.append((ir, ir.arg))
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
					cst += repeat((ir, None), ir.so)
				else:cst[-ir.var.count(None):]=repeat((ir,None), ir.so)
				break
			calcvar(ir, cst)
			ir.sd=True
			ir=ir.n
	def execir(ir):
		st=[]
		try:
			while True:ir=ir.eval(st)
		except:return ir
	def compile2(ir, bc):
		while ir.sd is True:
			ir.sd=len(bc)
			if ir.emit(bc) is ...:return
			ir=ir.n
		bc += jumpabs(ir.sd)
		if bc[ir.sd] is 113:bc[-2:]=bc[ir.sd+1:ir.sd+3]
	empty={}
	root=Op16(None)
	node14=Op14(None)
	ir=compile((X1,0),mvL)
	bc=bytearray()
	while True:
		node14.sd=True
		pg.clear()
		root.n=ir
		ir.si.add(root)
		peephole(ir)
		bc += loadmkconst(0)
		compile2(ir, bc)
		f=FunctionType(CodeType(0,0,0,65536,0,bytes(bc),tuple(constl),(),(),"","",0,b""),empty)()
		if f is None:return
		ret11pos = None
		node14.si.clear()
		bc.clear()
		pro.clear()
		ir=X0,Y0=X1,Y1=f[0]
		for x,y in ps.keys():
			X0=min(X0,x)
			X1=max(X1,x)
			Y0=min(Y0,y)
			Y1=max(Y1,y)
		WID=X1-X0+1
		HEI=Y1-Y0+1
		ir=tail=compile(ir, f[1])
		for x in range(2,len(f)):
			ir=Op0(f[x])
			ir.n=tail
			tail.si.add(ir)
			tail=ir
if __name__ == "__main__":
	from sys import argv
	main(open(argv[1],"rb"))
