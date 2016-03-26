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
	fiter = mkemit("FOR_ITER")
	lappend1 = mkemit("LIST_APPEND")(1)
	blist1 = mkemit("BUILD_LIST_UNPACK")(1)
	_not = mkemit("UNARY_NOT")
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
	def mkconst(c):
		nonlocal constl
		if c in consts:return consts[c]
		else:
			a=consts[c]=len(constl).to_bytes(2,"little")
			constl += c,
			return a
	ps = [32]*2560
	for y,line in enumerate(pro):
		if y>=25:break
		for x,c in enumerate(line):
			if x>=80:break
			ps[x<<5|y]=c
	pg={}
	consts={}
	pro=set()
	constl=[ps, pro]
	mvL=lambda i:i-2528 if i>=2528 else i+32
	mvK=lambda i:i-1 if i&31 else i+24
	mvH=lambda i:i+2528 if i<32 else i-32
	mvJ=lambda i:i+1 if (i&31)<24 else i-24
	si = b"\0\2\1\1\1\2\1\1\0\0\2\3\0\1\0\0\0"
	so = b"\1\1\1\0\2\2\0\0\1\1\1\0\0\0\0\0\0"
	bins = add, subtract, multiply, floordivide, modulo, cmpgt
	def op0(self, st):
		st.append(self.arg)
		return self.n
	def op1(self, st, a, b):
		arg = self.arg
		st.append(b+a if arg is add else
			b-a if arg is subtract else
			b*a if arg is multiply else
			b>a if arg is cmpgt else
			0 if not a else
			b//a if arg is floordivide else b%a)
		return self.n
	def op2(self, st, a):
		st.append(not a)
		return self.n
	def op3(self, st, a):return self.n
	def op4(self, st, a):
		st.append(a)
		st.append(a)
		return self.n
	def op5(self, st, a, b):
		st.append(a)
		st.append(b)
		return self.n
	def op6(self, st, a):
		sowrite("%d "%a)
		return self.n
	def op7(self, st, a):
		sowrite("%c"%a)
		return self.n
	def op8(self, st):
		st.append(getch())
		return self.n
	def op9(self, st):
		st.append(int(input()))
		return self.n
	def op10(self, st, a, b):
		a|=b<<5
		st.append(0<=a<2560 and ps[a])
		return self.n
	def op11(self, st, a, b, c):
		a|=b<<5
		if 0<=a<2560 and (a&31)<25:
			ps[a]=c
			if a in pro:
				pro.clear()
				return [*self.arg,*reversed(st)]
		return self.n
	def op12(self, st):
		c=getrandbits(2)
		return self.n if c==3 else self.arg[c]
	def op13(self, st, a):return self.n if a else self.arg
	def op14(self, st):return
	def op15(self, st):
		sowrite(self.arg)
		return self.n
	def op16(self, st):return self.n
	ops = op0, op1, op2, op3, op4, op5, op6, op7, op8, op9, op10, op11, op12, op13, op14, op15, op16
	def sguard(bc, x):
		if x==1:
			j1=len(bc)+1
			bc += jumpiforpop
			bc += loadmkconst(0)
			bc += loadmkconst(1)
			bc[j1],bc[j1+1]=len(bc).to_bytes(2,"little")
		elif x:
			j1=len(bc)+1
			bc += jump
			bc += loadmkconst(1)
			bc += add
			bc += loadmkconst(0)
			bc += swap
			bc[j1],bc[j1+1]=len(bc).to_bytes(2,"little")
			bc += dup
			bc += loadmkconst(x-1)
			bc += cmpgt
			bc += jumpifnot
			bc[-2],bc[-1]=(j1+2).to_bytes(2,"little")
	def emit0(self, bc):
		bc += loadmkconst(1)
		bc += add
		bc += loadmkconst(self.arg)
		bc += swap
	def emit1(self, bc):
		a,b=self.var
		if a is None and b is None:
			if self.dep<2:sguard(bc, 2)
			bc += loadmkconst(-1)
			bc += add
			bc += rot3
			bc += self.arg
			bc += swap
		else:
			if a is not None:
				if not self.dep:sguard(bc, 1)
				bc += swap
				bc += loadmkconst(a)
			else:
				bc += swap
				bc += loadmkconst(b)
				bc += swap
			bc += self.arg
			bc += swap
	def emit2(self, bc):
		if not self.dep:sguard(bc, 1)
		bc += swap
		bc += _not
		bc += swap
	def emit3(self, bc):
		if not self.dep:
			bc += dup
			jt = len(bc)+1
			bc += jumpifnot
		bc += loadmkconst(-1)
		bc += add
		bc += swap
		bc += pop
		if not self.dep:bc[jt],bc[jt+1]=len(bc).to_bytes(2,"little")
	def emit4(self, bc):
		if not self.dep:sguard(bc, 1)
		bc += loadmkconst(1)
		bc += add
		bc += swap
		bc += dup
		bc += rot3
		bc += swap
	def emit5(self, bc):
		a,b=self.var
		if a is None and b is None:
			if self.dep<2:sguard(bc, 2)
			bc += rot3
			bc += swap
			bc += rot3
			bc += rot3
		elif a is not None:
			if not self.dep:sguard(bc, 1)
			bc += loadmkconst(1)
			bc += add
			bc += loadmkconst(a)
			bc += rot3
		else:
			bc += loadmkconst(1)
			bc += add
			bc += loadmkconst(b)
			bc += swap
	def emit6(self, bc):
		if not self.dep:sguard(bc, 1)
		bc += loadmkconst(-1)
		bc += add
		bc += swap
		bc += loadmkconst("%d ")
		bc += swap
		bc += modulo
		bc += loadmkconst(sowrite)
		bc += swap
		bc += call1
		bc += pop
	def emit7(self, bc):
		if not self.dep:sguard(bc, 1)
		bc += loadmkconst(-1)
		bc += add
		bc += swap
		bc += loadmkconst("%c")
		bc += swap
		bc += modulo
		bc += loadmkconst(sowrite)
		bc += swap
		bc += call1
		bc += pop
	def emit8(self, bc):
		bc += loadmkconst(1)
		bc += add
		bc += loadmkconst(getch)
		bc += call0
		bc += swap
	def emit9(self, bc, intput=lambda:int(input())):
		bc += loadmkconst(1)
		bc += add
		bc += loadmkconst(intput)
		bc += call0
		bc += swap
	def emit10h(bc):
		bc += dup
		bc += loadmkconst(0)
		bc += cmplt
		j1 = len(bc)+1
		bc += jumpif
		bc += dup
		bc += loadmkconst(2560)
		bc += cmpgte
		j2 = len(bc)+1
		bc += jumpif
		bc += loadconst(0)
		bc += swap
		bc += subscr
		j3 = len(bc)+1
		bc += jump
		bc[j1],bc[j1+1]=bc[j2],bc[j2+1]=len(bc).to_bytes(2,"little")
		bc += _not
		bc[j3],bc[j3+1]=len(bc).to_bytes(2,"little")
		bc += swap
	def emit10(self, bc):
		a,b = self.var
		if a is None and b is None:
			if self.dep<2:sguard(bc, 2)
			bc += loadmkconst(-1)
			bc += add
			bc += rot3
			bc += swap
			bc += loadmkconst(5)
			bc += lshift
			bc += bor
			return emit10h(bc)
		elif a is not None and b is not None:
			bc += loadmkconst(1)
			bc += add
			a|=b<<5
			if 0<=a<2560:
				bc += loadconst(0)
				bc += loadmkconst(a)
				bc += subscr
			else:bc += loadmkconst(0)
			bc += swap
		elif a is not None:
			if not self.dep:sguard(bc, 1)
			bc += swap
			if 0<=a<25:
				bc += loadmkconst(5)
				bc += lshift
				if a:
					bc += loadmkconst(a)
					bc += bor
				return emit10h(bc)
			else:
				bc += pop
				bc += loadmkconst(0)
				bc += swap
		else:
			bc += swap
			if 0<=b<80:
				if b:
					bc += loadmkconst(b<<5)
					bc += bor
				return emit10h(bc)
			else:
				bc += pop
				bc += loadmkconst(0)
				bc += swap
	def wmem(arg):
		def f(s):
			pro.clear()
			consts.clear()
			del constl[2:]
			return iter(repeat(s,s)),[*arg]
		return f
	def emit11ret(bc):
		bc += swap
		bc += call1
		bc += unpack2
		j1 = len(bc).to_bytes(2,"little")
		bc += fiter(10)
		bc += pop
		bc += rot3
		bc += swap
		bc += lappend1
		bc += swap
		bc += jump
		bc[-2],bc[-1]=j1
		bc += ret
		return ...
	def emit11(self, bc):
		a,b,c=self.var
		if a is None and b is None and c is None:
			if self.dep<3:sguard(bc, 3)
			bc += loadmkconst(-3)
			bc += add
			bc += rot3
			bc += swap
			bc += loadmkconst(5)
			bc += lshift
			bc += bor
			bc += dup
			bc += loadmkconst(0)
			bc += cmplt
			j1 = len(bc)+1
			bc += jumpif
			bc += dup
			bc += loadmkconst(2560)
			bc += cmpgte
			j2 = len(bc)+1
			bc += jumpif
			bc += dup
			bc += loadmkconst(31)
			bc += band
			bc += loadmkconst(25)
			bc += cmpgte
			j3 = len(bc)+1
			bc += jumpif
			bc += swap
			bc += rot3
			bc += dup
			bc += rot3
			bc += loadconst(0)
			bc += swap
			bc += stscr
			bc += loadconst(1)
			bc += cmpin
			j4 = len(bc)+1
			bc += jumpifnot
			bc += loadmkconst(wmem(self.arg))
			emit11ret(bc)
			bc[j1],bc[j1+1]=bc[j2],bc[j2+1]=bc[j3],bc[j3+1]=len(bc).to_bytes(2,"little")
			bc += pop
			bc[j4],bc[j4+1]=len(bc).to_bytes(2,"little")
		elif a is not None and b is not None:
			a|=b<<5
			if c is not None:
				if 0<=a<2560:
					bc += loadmkconst(c)
					bc += loadconst(0)
					bc += loadmkconst(a)
					bc += stscr
					if a in pro:
						bc += loadmkconst(wmem(self.arg))
						return emit11ret(bc)
			elif 0<=a<2560:
				if not self.dep:sguard(bc, 1)
				bc += loadmkconst(-1)
				bc += add
				bc += swap
				bc += loadconst(0)
				bc += loadmkconst(a)
				bc += stscr
				if a in pro:
					bc += loadmkconst(wmem(self.arg))
					return emit11ret(bc)
			else:emit3(self, bc)
		else:
			if c is not None:
				if not self.dep:sguard(bc, 1)
				bc += loadmkconst(-1)
			elif self.dep<2:
				sguard(bc, 2)
				bc += loadmkconst(-2)
			bc += add
			bc += rot3
			bc += swap
			if b is None:
				bc += loadmkconst(5)
				bc += lshift
				bc += loadmkconst(a)
			else:
				bc += loadmkconst(b<<5)
			bc += bor
			bc += dup
			bc += loadmkconst(0)
			bc += cmplt
			j1 = len(bc)+1
			bc += jumpif
			bc += dup
			bc += loadmkconst(2560)
			bc += cmpgte
			j2 = len(bc)+1
			bc += jumpif
			bc += dup
			bc += loadmkconst(31)
			bc += band
			bc += loadmkconst(25)
			bc += cmpgte
			j3 = len(bc)+1
			bc += jumpif
			bc += swap
			bc += rot3
			bc += dup
			bc += rot3
			bc += loadconst(0)
			bc += swap
			if c is not None:
				bc += loadmkconst(c)
				bc += rot3
			bc += stscr
			bc += loadconst(1)
			bc += cmpin
			j4 = len(bc)+1
			bc += jumpifnot
			bc += loadmkconst(wmem(self.arg))
			emit11ret(bc)
			bc[j1],bc[j1+1]=bc[j2],bc[j2+1]=bc[j3],bc[j3+1]=len(bc).to_bytes(2,"little")
			if c is None:bc += pop
			bc[j4],bc[j4+1]=len(bc).to_bytes(2,"little")
	def emit12(self, bc):
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
	def emit13(self, bc):
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
	def emit14(self, bc):
		bc += loadmkconst(None)
		bc += ret
		return ...
	def emit15(self, bc):
		bc += loadmkconst(sowrite)
		bc += loadmkconst(self.arg)
		bc += call1
		bc += pop
	def emit16(self, bc):return
	emits = emit0, emit1, emit2, emit3, emit4, emit5, emit6, emit7, emit8, emit9, emit10, emit11, emit12, emit13, emit14, emit15, emit16
	class Inst:
		__slots__ = "n", "op", "arg", "var", "sd", "dep", "si"
		def __init__(self, op=16, arg=None):
			self.n = None
			self.op = op
			self.arg = arg
			self.var = ((),(None,),(None,None),(None,None,None))[si[op]]
			self.sd = False
			self.dep = 0
			self.si = set()
		def __str__(self, names=("ld","bin","not","pop","dup","swp","pui","puc","gc","gi","ldm","stm","rj","jz","ret","pus","nop"),
			blut={add:"+", subtract:"-", multiply:"*", floordivide:"/", modulo:"%", cmpgt:">"}):
			return "%d"%id(self) if self.op is None else "%s\t%s\t%s"%(names[self.op],blut[self.arg] if self.op==1 else self.arg,self.var)
		def eval(self, st):return ops[self.op](self, st, *((c if c is not None else st.pop() if st else 0) for c in self.var))
		def emit(self, bc):return emits[self.op](self, bc)
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
	def compile(i,mv):
		def emit(op, arg=None):
			nonlocal inst
			pist.clear()
			tail=inst
			inst=Inst()
			tail.op=op
			tail.arg=arg
			tail.n=inst
			tail.var = ((),(None,),(None,None),(None,None,None))[si[op]]
			inst.si.add(tail)
			return tail
		head=inst=Inst()
		pist=[]
		while True:
			i=mv(i)
			imv=i,mv
			if imv in pg:
				i2=pg[imv]
				if inst is not i2:
					for i in pist:pg[i]=i2
					if inst is head:return i2
					for i in inst.si:
						i.n=i2
						i2.si.add(i)
				return head
			pg[imv]=inst
			pist.append(imv)
			pro.add(i)
			i2 = ps[i]
			if 33<=i2<=126:
				i2=b'\x10\x1d\x1f\x11\x0e\x17$$$\x0c\n\x15\x0b\x14\r\0\1\2\3\4\5\6\7\x08\t\x12$"$ \x1a\x1e$$$$$$$$$$$$$$$$$$$$$$$$$$$\x13$!\x1c\x0f$$$$$$\x18$$$$$$$$\x19$$$$$#$$$$$\x1b$\x16'[i2-33]
				if i2<10:emit(0, i2)
				elif i2<16:emit(1, bins[i2-10])
				elif i2<25:emit(i2-14)
				elif i2==36:continue
				elif i2==25:emit(11, imv)
				elif i2==26:
					i2=emit(12, [compile(i,mvL), compile(i,mvK), compile(i,mvH)])
					for mv in i2.arg:mv.si.add(i2)
					mv=mvJ
				elif i2==27:
					i2=emit(13, compile(i,mvJ))
					i2.arg.si.add(i2)
					mv=mvK
				elif i2==28:
					i2=emit(13, compile(i,mvL))
					i2.arg.si.add(i2)
					mv=mvH
				elif i2==29:
					while True:
						i=mv(i)
						pro.add(i)
						i2=ps[i]
						if i2==34:break
						emit(0, i2)
				elif i2==30:
					emit(14)
					return head
				elif i2==31:i=mv(i)
				elif i2==32:mv=mvL
				elif i2==33:mv=mvK
				elif i2==34:mv=mvH
				else:mv=mvJ
	def calcvar(lir, ir, cst):
		def calcvarhelper():
			a=-1
			b=-len(cst)
			for x in range(siop):
				x=a-x
				if x<=a+b:yield None
				else:
					c0,c1=cst[x]
					yield c1
					if c1 is not None:
						del cst[x]
						c0.op=16
						c0.var=()
						a+=1
		while ir.op == 16:
			if lir is ir:return
			ir.si.remove(lir)
			ir=lir.n=ir.n
			ir.si.add(lir)
		if not cst:return
		siop=ir.var.count(None)
		if not siop:
			ir.dep=len(cst)
			return
		print(lir.n is ir, lir in ir.si, lir, ir, [c[1] for c in cst], *ir.si)
		if ir.op==13:
			if cst[-1][1] is not None:
				c0,c1=cst.pop()
				print("#",lir, ir,"#",c0,"#", ir.n,ir.arg, [c[1] for c in cst])
				c0.op=16
				c0.var=()
				lir.n = ir.n if c1 else ir.arg
				lir.n.si.add(lir)
				ir.si.remove(lir)
				if not ir.si:
					ir.n.si.remove(ir)
					ir.arg.si.remove(ir)
				return calcvar(lir, lir.n, cst)
			elif len(ir.si)==1:ir.dep=len(cst)
			return
		elif ir.op==4 and ir.n.op in (3,5):
			ir.n.si.remove(ir)
			ir.n=ir.n.n
			ir.n.si.add(ir)
			if ir.n.op==3:
				ir.remove()
				return calcvar(lir, lir.n, cst)
		if len(ir.si)>1:
			print("~", lir, ",", lir.n, ":", ir, ",", ir.n, ":", *ir.si, lir in ir.si)
			if any(a is not None for a,a in cst[-siop:]):
				ir.si.remove(lir)
				a=ir.n
				lir.n=ir=Inst(ir.op, ir.arg)
				ir.si.add(lir)
				ir.n=a
				a.si.add(ir)
				print("~~", lir, ir, [c for c,c in cst])
				return calcvar(lir, ir, cst)
			else:return
		ir.var=(*calcvarhelper(),)
		ir.dep=len(cst)
	def peephole(ir):
		cst=[]
		while True:
			while True:
				if ir.sd:return
				op=ir.op
				print("$",ir,[c[1] for c in cst])
				if not op:
					cst.append((ir, ir.arg))
					break
				elif op==13:
					if ir.n is ir.arg:
						op=ir.op=3
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
				elif op == 14:
					ir.sd=True
					return
				if si[op]:
					siop=ir.var.count(None)
					if not siop:
						if op<8:
							if op==3:ir.remove()
							elif op==4:
								ir.sd=True
								c=ir.var[0]
								ir.op=0
								ir.arg=c
								ir.var=()
								a=ir.n
								ir.n=b=Inst(0, c)
								b.si.add(ir)
								b.n=a
								a.si.remove(ir)
								a.si.add(b)
								cst += (ir, c), (b, c)
								calcvar(b, a, cst)
								ir=b.n
								continue
							elif op==5:
								ir.sd=True
								ir.op=0
								ir.arg=ir.var[0]
								a=ir.n
								ir.n=b=Inst(0, ir.var[1])
								b.si.add(ir)
								b.n=a
								a.si.remove(ir)
								a.si.add(b)
								cst += zip((b, a), ir.var)
								ir.var=()
								calcvar(b, a, cst)
								ir=b.n
								continue
							elif op in (6,7):
								ir.op=15
								ir.arg=("%d " if op==6 else "%c")%ir.var
								ir.var=()
							else:
								x=[]
								ir.eval(x)
								ir.op=0
								ir.arg=x[0]
								ir.var=()
								cst.append((ir, ir.arg))
							break
					elif len(ir.si)>1:
						cst.clear()
						ir.dep=0
				cst[-siop:]=repeat((ir,None), so[op])
				break
			calcvar(ir, ir.n, cst)
			ir.sd=True
			ir=ir.n
	def execir(ir):
		st=[]
		while True:
			ir=ir.eval(st)
			if type(ir) is not Inst:return ir
	def compile2(ir, bc):
		while True:
			if ir.sd is not True and ir.sd is not False:
				#print("%%%d jmp %d"%(len(bc), ir.sd))
				bc += jumpabs(ir.sd)
				return
			ir.sd=len(bc)
			#if len(ir.si)>1:print("\t",*ir.si)
			#print("%%%d"%ir.sd, ir)
			#if ir.op != 16:Inst(15, "%s\n"%ir).emit(bc)
			if ir.emit(bc) is ...:return
			ir=ir.n
	empty={}
	root=Inst()
	root.n=ir=compile(2528,mvL)
	ir.si.add(root)
	bc=bytearray()
	while True:
		pg.clear()
		peephole(ir)
		#f=execir(ir)
		bc += loadmkconst(0)
		compile2(ir, bc)
		f=FunctionType(CodeType(0,0,0,65536,0,bytes(bc),tuple(constl),(),(),"","",0,b""),empty)()
		#from dis import dis;dis(f);f=f()
		if f is None:return
		bc.clear()
		ir=tail=compile(f[0], f[1])
		for x in range(2,len(f)):
			ir=Inst(0, f[x])
			tail.si.add(ir)
			ir.n=tail
			tail=ir
		root.n=ir
		ir.si.add(root)
if __name__ == "__main__":
	from sys import argv
	main(open(argv[1],"rb"))