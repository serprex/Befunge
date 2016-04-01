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
	bor = mkemit("BINARY_OR")
	band = mkemit("BINARY_AND")
	subscr = mkemit("BINARY_SUBSCR")
	stscr = mkemit("STORE_SUBSCR")
	unpack2 = mkemit("UNPACK_SEQUENCE")(2)
	tuple2 = mkemit("BUILD_TUPLE")(2)
	fiter = mkemit("FOR_ITER")
	lappend1 = mkemit("LIST_APPEND")(1)
	blist1 = mkemit("BUILD_LIST_UNPACK")(1)
	_not = mkemit("UNARY_NOT")
	_neg = mkemit("UNARY_NEGATIVE")
	ret = mkemit("RETURN_VALUE")
	cmp = mkemit("COMPARE_OP")
	cmplt = cmp(0)
	cmpeq = cmp(2)
	cmpgt = cmp(4)
	cmpgte = cmp(5)
	cmpin = cmp(6)
	call = mkemit("CALL_FUNCTION")
	call0 = call(0)
	call1 = call(1)
	loadconst = mkemit("LOAD_CONST")
	loadmkconst = lambda a:b"d"+mkconst(a)
	jumpabs = mkemit("JUMP_ABSOLUTE")
	jump = jumpabs(0)
	jumpiforpop = opmap["JUMP_IF_TRUE_OR_POP"].to_bytes(3,"little")
	jumpifnotorpop = opmap["JUMP_IF_FALSE_OR_POP"].to_bytes(3,"little")
	jumpif = opmap["POP_JUMP_IF_TRUE"].to_bytes(3,"little")
	jumpifnot = opmap["POP_JUMP_IF_FALSE"].to_bytes(3,"little")
	addply = add + multiply
	def mkconst(c):
		nonlocal constl
		if c in consts:return consts[c]
		else:
			a=consts[c]=len(constl).to_bytes(2,"little")
			constl += c,
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
		def __init__(self, arg=None):
			self.arg = self.n = None
			self.var = self.novar
			self.sd = False
			self.dep = 0
			self.si = set()
		def __str__(self, names=("ld","bin","not","pop","dup","swp","pui","puc","gc","gi","ldm","stm","rj","jz","ret","pus","nop"),
			blut={add:"+", subtract:"-", multiply:"*", floordivide:"/", modulo:"%", cmpgt:">"}):
			return "%s\t%s\t%s"%(names[self.op],blut[self.arg] if self.op==1 else self.arg,self.var)
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
				elif x==dep:
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
					bc[-2],bc[-1]=(j1+2).to_bytes(2,"little")
		def remove(self):
			sn=self.n
			sn.si.remove(self)
			for s in self.si:
				sn.si.add(s)
				if s.n is self:s.n=sn
				if s.arg is self:s.arg=sn
				elif s.op == 12:
					for sa in 0,1,2:
						if s.arg[sa] is self:s.arg[sa]=sn
	class Op0(Inst):
		__slots__ = ()
		op=0
		siop=0
		so=1
		novar=()
		def __init__(self, arg):
			self.n = None
			self.arg = arg
			self.var = ()
			self.sd = False
			self.dep = 0
			self.si = set()
		def emit(self, bc):
			bc += loadmkconst(1)
			bc += add
			bc += loadmkconst(self.arg)
			bc += swap
		def eva(self, st):
			st.append(self.arg)
			return self.n
	class Op1(Inst):
		__slots__ = ()
		op=1
		siop=2
		so=1
		novar=(None, None)
		def __init__(self, arg):
			self.n = None
			self.arg = arg
			self.var = self.novar
			self.sd = False
			self.dep = 0
			self.si = set()
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
	class Op2(Inst):
		__slots__ = ()
		op=2
		si=1
		so=1
		novar=(None,)
		def emit(self, bc):
			self.sguard(bc, 0)
			bc += swap
			bc += _not
			bc += swap
		def eva(self, st, a):
			st.append(not a)
			return self.n
	class Op3(Inst):
		__slots__ = ()
		op=3
		siop=1
		so=0
		novar=(None,)
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
	class Op4(Inst):
		__slots__ = ()
		op=4
		siop=1
		so=2
		novar=(None,)
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
	class Op5(Inst):
		__slots__ = ()
		op=5
		siop=2
		so=2
		novar=(None, None)
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
	class Op6(Inst):
		__slots__ = ()
		op=6
		siop=1
		so=0
		novar=(None,)
		def __init__(self, arg):
			self.n = None
			self.arg = arg
			self.var = (None,)
			self.sd = False
			self.dep = 0
			self.si = set()
		def emit(self, bc):
			self.sguard(bc, 0)
			bc += loadmkconst(-1)
			bc += add
			bc += swap
			bc += loadmkconst(self.arg)
			bc += swap
			bc += modulo
			bc += loadmkconst(sowrite)
			bc += swap
			bc += call1
			bc += pop
		def eva(self, st, a):
			sowrite(self.arg%a)
			return self.n
	class Op8(Inst):
		__slots__ = ()
		op=8
		siop=0
		so=1
		novar=()
		def emit(self, bc):
			bc += loadmkconst(1)
			bc += add
			bc += loadmkconst(getch)
			bc += call0
			bc += swap
		def eva(self, st):
			st.append(getch())
			return self.n
	class Op9(Inst):
		__slots__ = ()
		op=9
		siop=0
		so=1
		novar=()
		def emit(self, bc, intput=lambda:int(input())):
			bc += loadmkconst(1)
			bc += add
			bc += loadmkconst(intput)
			bc += call0
			bc += swap
		def eva(self, st):
			st.append(int(input()))
			return self.n
	emit10h = tuple2 + loadconst(0) + swap + subscr + swap
	class Op10(Inst):
		__slots__ = ()
		op=10
		siop=2
		so=1
		novar=(None, None)
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
	wmem = lambda arg:lambda s:(iter(repeat(s,s)),[*arg])
	def emit11ret(bc):
		nonlocal ret11pos
		if ret11pos is None:
			ret11pos = len(bc)
			bc += swap
			bc += call1
			bc += unpack2
			j1 = (ret11pos+7).to_bytes(2,"little")
			bc += fiter(10)
			bc += pop
			bc += rot3
			bc += swap
			bc += lappend1
			bc += swap
			bc += jump
			bc[-2],bc[-1]=j1
			bc += ret
		else:bc += jumpabs(ret11pos)
		return ...
	class Op11(Inst):
		__slots__ = ()
		op=11
		siop=3
		so=0
		novar=(None, None, None)
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
				bc += loadmkconst(wmem(self.arg))
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
					bc += loadmkconst(wmem(self.arg))
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
				bc += loadmkconst(wmem(self.arg))
				emit11ret(bc)
				bc[j4],bc[j4+1]=len(bc).to_bytes(2,"little")
		def eva(self, st, a, b, c):
			a=b,a
			ps[a]=c
			if a in pro:
				pro.clear()
				return [*self.arg,*reversed(st)]
			return self.n
	class Op12(Inst):
		__slots__ = ()
		op=12
		siop=0
		so=0
		novar=()
		def __init__(self, arg):
			self.n = None
			self.arg = arg
			self.var = self.novar
			self.sd = False
			self.dep = 0
			self.si = set()
		def emit(self, bc):
			bc += loadmkconst(getrandbits)
			bc += loadmkconst(2)
			bc += call1
			bc += dup
			j1 = len(bc)+1
			bc += jumpifnot
			bc += dup
			bc += loadmkconst(1)
			bc += cmpeq
			j2 = len(bc)+1
			bc += jumpif
			bc += dup
			bc += loadmkconst(2)
			bc += cmpeq
			j3 = len(bc)+1
			bc += jumpif
			bc += pop
			compile2(self.arg[0], bc)
			bc[j1],bc[j1+1]=len(bc).to_bytes(2,"little")
			bc += pop
			compile2(self.arg[1], bc)
			bc[j2],bc[j2+1]=len(bc).to_bytes(2,"little")
			bc += pop
			compile2(self.arg[2], bc)
			bc[j3],bc[j3+1]=len(bc).to_bytes(2,"little")
			bc += pop
		def eva(self, st):
			c=getrandbits(2)
			return self.n if c==3 else self.arg[c]
	class Op13(Inst):
		__slots__ = ()
		op=13
		siop=1
		so=0
		novar=(None,)
		def __init__(self, arg):
			self.n = None
			self.arg = arg
			self.var = self.novar
			self.sd = False
			self.dep = 0
			self.si = set()
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
			j2 = len(bc)+1
			bc += jumpif
			bc[j3],bc[j3+1]=len(bc).to_bytes(2,"little")
			compile2(self.arg, bc)
			bc[j2],bc[j2+1]=len(bc).to_bytes(2,"little")
		def eva(self, st, a):return self.n if a else self.arg
	class Op14(Inst):
		__slots__ = ()
		op=14
		siop=0
		so=0
		novar=()
		def emit(self, bc):
			bc += loadmkconst(None)
			bc += ret
			return ...
		def eva(self, st):return
	class Op15(Inst):
		__slots__ = ()
		op=15
		siop=0
		so=0
		novar=()
		def __init__(self, arg):
			self.n = None
			self.arg = arg
			self.var = self.novar
			self.sd = False
			self.dep = 0
			self.si = set()
		def emit(self, bc):
			bc += loadmkconst(sowrite)
			bc += loadmkconst(self.arg)
			bc += call1
			bc += pop
		def eva(self, st):
			sowrite(self.arg)
			return self.n
	class Op16(Inst):
		__slots__ = ()
		op=16
		siop=0
		so=0
		novar=()
		def __init__(self):
			self.n = None
			self.sd = False
			self.dep = 0
			self.si = set()
		def emit(self, bc):return
		def eva(self, st):return self.n
	emits = Op0, Op1, Op2, Op3, Op4, Op5, Op6, None, Op8, Op9, Op10, Op11, Op12, Op13, Op14, Op15, Op16
	def compile(i,mv):
		def emit(op, arg=None):
			nonlocal inst
			pist.clear()
			tail=inst
			inst=Op16()
			tail.__class__=op
			tail.n=inst
			tail.arg=arg
			tail.var=tail.novar
			inst.si.add(tail)
			return tail
		head=inst=Op16()
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
				elif i2 in (20,21):emit(Op6, ("%c" if i2==21 else "%d "))
				elif i2<25:emit(emits[i2-14])
				elif i2==36:continue
				elif i2==25:emit(Op11, imv)
				elif i2==26:
					i2=emit(Op12, (compile(i,mvL), compile(i,mvK), compile(i,mvH)))
					for mv in i2.arg:mv.si.add(i2)
					mv=mvJ
				elif i2==27:
					i2=emit(Op13, compile(i,mvJ))
					i2.arg.si.add(i2)
					mv=mvK
				elif i2==28:
					i2=emit(Op13, compile(i,mvL))
					i2.arg.si.add(i2)
					mv=mvH
				elif i2==29:
					while True:
						i=mv(*i)
						pro.add(i)
						i2=ps[i]
						if i2==34:break
						emit(Op0, i2)
				elif i2==30:
					for i in pist:pg[i]=node14
					if inst is head:return node14
					for i in inst.si:
						i.n=node14
						node14.si.add(i)
					return head
				elif i2==31:i=mv(*i)
				elif i2==32:mv=mvL
				elif i2==33:mv=mvK
				elif i2==34:mv=mvH
				else:mv=mvJ
	def calcvar(lir, cst):
		if not cst:return
		ir=lir.n
		def calcvarhelper():
			a=-1
			b=-len(cst)
			for x in range(ir.siop):
				x=a-x
				if x<=a+b:yield None
				else:
					c0,c1=cst[x]
					yield c1
					if c1 is not None:
						del cst[x]
						c0.__class__ = Op16
						c0.var=()
						a+=1
		while ir.op == 16:
			if lir is ir:return
			ir.si.remove(lir)
			ir=lir.n=ir.n
			ir.si.add(lir)
		if not ir.var:
			ir.dep=len(cst)
			return
		if ir.op==13:
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
			elif len(ir.si)==1:ir.dep=len(cst)
			return
		elif ir.op==4:
			if ir.n.op in (3,5):
				opn=ir.n.op
				ir.n.si.remove(ir)
				ir.n=ir.n.n
				ir.n.si.add(ir)
				if opn==3:
					ir.remove()
					return calcvar(lir, cst)
			else:
				b=cst[-1][1]
				if b is not None:
					if len(ir.si)>1:
						ir.si.remove(lir)
						a=ir.n
						lir.n=ir=Op0(b)
						ir.si.add(lir)
						ir.n=a
						a.si.add(ir)
						return
					else:
						ir.__class__=Op0
						ir.arg=b
						ir.var=()
				elif len(ir.si)==1:ir.dep=len(cst)
				return
		if len(ir.si)>1:
			if any(a is not None for a,a in cst[-ir.siop:]):
				ir.si.remove(lir)
				a=ir.n
				lir.n=ir=type(ir)(ir.arg)
				ir.si.add(lir)
				ir.n=a
				a.si.add(ir)
				return calcvar(lir, cst)
		else:
			ir.var=(*calcvarhelper(),)
			ir.dep=len(cst)
	def peephole(ir):
		cst=[]
		while True:
			while True:
				if ir.sd:return
				op=ir.op
				if not op:
					if len(ir.si)>1:cst.clear()
					cst.append((ir, ir.arg))
					break
				elif op==13:
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
				elif op==12:
					ir.sd=True
					for a in ir.arg:peephole(a)
					ir=ir.n
					cst.clear()
					continue
				elif op==11:
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
				siop=ir.var.count(None)
				if not siop:
					if op<8:
						if op==1:
							ir.__class__=Op0
							c=ir.arg
							a,b=ir.var
							a=ir.arg=(b+a if c is add else
								b-a if c is subtract else
								b*a if c is multiply else
								b>a if c is cmpgt else
								0 if not a else
								b//a if c is floordivide else b%a)
							ir.var=()
							cst.append((ir, a))
						elif op==2:
							ir.__class__=Op0
							a,=ir.var
							a=ir.arg=not a
							ir.var=()
							cst.append((ir, a))
						elif op==3:
							calcvar(ir, cst)
							ir.remove()
							ir=ir.n
							continue
						elif op==4:
							ir.sd=True
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
							cst += (ir, c), (b, c)
							ir=b
						elif op==5:
							c,x=ir.var
							ir.sd=True
							ir.__class__=Op0
							ir.arg=c
							a=ir.n
							ir.n=b=Op0(x)
							b.si.add(ir)
							b.n=a
							a.si.remove(ir)
							a.si.add(b)
							cst += (ir, c), (b, x)
							ir.var=()
							ir=b
						else:
							ir.arg%=ir.var
							ir.__class__=Op15
							ir.var=()
					else:cst += repeat((ir, None), ir.so)
				else:
					if len(ir.si)>1:
						cst.clear()
						ir.dep=0
					cst[-siop:]=repeat((ir,None), ir.so)
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
		while True:
			if ir.sd is not True and ir.sd is not False:
				bc += jumpabs(ir.sd)
				return
			ir.sd=len(bc)
			if ir.emit(bc) is ...:return
			ir=ir.n
	empty={}
	root=Op16()
	node14=Op14()
	ir=compile((X1,0),mvL)
	bc=bytearray()
	while True:
		node14.sd = True
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
		consts.clear()
		del constl[2:]
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
