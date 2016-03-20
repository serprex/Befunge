#!/bin/python
def getch():
	try:from termios import tcgetattr,tcsetattr,TCSANOW
	except ImportError:
		from msvcrt import getch
		return lambda:ord(getch())
	from sys import stdin
	def getch():
		print(end="",flush=True)
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
	ps = [0]*2560
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
	#    0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
	si = b"\0\2\1\1\1\2\1\1\0\0\2\3\0\1\0\0"
	so = b"\1\1\1\0\2\2\0\0\1\1\1\0\0\0\0\0"
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
		st.append(b)
		st.append(a)
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
		st.append(ps[a] if 0<=b<2560 else 0)
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
	ops = op0, op1, op2, op3, op4, op5, op6, op7, op8, op9, op10, op11, op12, op13, op14, op15
	def patch(bc, n, x):
		bc[n+1] = x&255
		bc[n+2] = x>>8
	def sguard(bc, x):
		if x==1:
			j1=len(bc)
			bc += jumpiforpop
			bc += loadmkconst(0)
			bc += loadmkconst(1)
			patch(bc, j1, len(bc))
		elif x:
			j1=len(bc)
			bc += jump
			bc += loadmkconst(1)
			bc += add
			bc += loadmkconst(0)
			bc += swap
			patch(bc, j1, len(bc))
			bc += dup
			bc += loadmkconst(x-1)
			bc += cmpgt
			bc += jumpifnot
			patch(bc, len(bc)-3, j1+3)
	def emit0(self, bc):
		bc += loadmkconst(1)
		bc += add
		bc += loadmkconst(self.arg)
		bc += swap
	def emit1(self, bc):
		a,b=self.var
		if a is None and b is None:
			sguard(bc, 2)
			bc += loadmkconst(-1)
			bc += add
			bc += rot3
			bc += self.arg
			bc += swap
		else:
			if a is not None:
				sguard(bc, 1)
				bc += swap
				bc += loadmkconst(a)
			else:
				bc += swap
				bc += loadmkconst(b)
				bc += swap
			bc += self.arg
			bc += swap
	def emit2(self, bc):
		sguard(bc, 1)
		bc += swap
		bc += _not
		bc += swap
	def emit3(self, bc):
		bc += dup
		jt = len(bc)
		bc += jumpifnot
		bc += loadmkconst(-1)
		bc += add
		bc += swap
		bc += pop
		patch(bc, jt, len(bc))
	def emit4(self, bc):
		sguard(bc, 1)
		bc += loadmkconst(1)
		bc += add
		bc += swap
		bc += dup
		bc += rot3
		bc += swap
	def emit5(self, bc):
		a,b=self.var
		if a is None and b is None:
			sguard(bc, 2)
			bc += rot3
			bc += swap
			bc += rot3
			bc += rot3
		elif a is not None:
			sguard(bc, 1)
			bc += loadmkconst(a)
			bc += rot3
		else:
			bc += loadmkconst(a)
			bc += swap
	def emit6(self, bc):
		sguard(bc, 1)
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
		sguard(bc, 1)
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
		j1 = len(bc)
		bc += jumpif
		bc += dup
		bc += loadmkconst(2560)
		bc += cmpgte
		j2 = len(bc)
		bc += jumpif
		bc += loadconst(0)
		bc += swap
		bc += subscr
		j3 = len(bc)
		bc += jump
		patch(bc, j1, len(bc))
		patch(bc, j2, len(bc))
		bc += _not
		patch(bc, j3, len(bc))
		bc += swap
	def emit10(self, bc):
		a,b = self.var
		if a is None and b is None:
			sguard(bc, 2)
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
			sguard(bc, 1)
			bc += swap
			bc += loadmkconst(5)
			bc += lshift
			if a:
				bc += loadmkconst(a)
				bc += bor
			return emit10h(bc)
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
		j1 = len(bc)
		bc += fiter(10)
		bc += pop
		bc += rot3
		bc += swap
		bc += lappend1
		bc += swap
		bc += jump
		patch(bc, len(bc)-3, j1)
		bc += ret
		return ...
	def emit11(self, bc):
		a,b,c=self.var
		if a is None and b is None and c is None:
			sguard(bc, 3)
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
			j1 = len(bc)
			bc += jumpif
			bc += dup
			bc += loadmkconst(2560)
			bc += cmpgte
			j2 = len(bc)
			bc += jumpif
			bc += dup
			bc += loadmkconst(31)
			bc += band
			bc += loadmkconst(25)
			bc += cmpgte
			j3 = len(bc)
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
			j4 = len(bc)
			bc += jumpifnot
			bc += loadmkconst(wmem(self.arg))
			emit11ret(bc)
			patch(bc, j1, len(bc))
			patch(bc, j2, len(bc))
			patch(bc, j3, len(bc))
			bc += pop
			patch(bc, j4, len(bc))
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
				sguard(bc, 1)
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
			raise NotImplemented("Still need to handle (a^b) p")
	def emit12(self, bc):
		bc += loadmkconst(getrandbits)
		bc += loadmkconst(2)
		bc += call1
		bc += dup
		j1 = len(bc)
		bc += jumpifnot
		bc += dup
		bc += loadmkconst(1)
		bc += cmpeq
		j2 = len(bc)
		bc += jumpif
		bc += dup
		bc += loadmkconst(2)
		bc += cmpeq
		j3 = len(bc)
		bc += jumpif
		bc += pop
		compile2(self.arg[0], bc)
		patch(bc, j1, len(bc))
		bc += pop
		compile2(self.arg[1], bc)
		patch(bc, j2, len(bc))
		bc += pop
		compile2(self.arg[2], bc)
		patch(bc, j3, len(bc))
		bc += pop
	def emit13(self, bc):
		j1 = len(bc)
		bc += jumpiforpop
		bc += loadmkconst(0)
		bc += dup
		patch(bc, j1, len(bc))
		bc += loadmkconst(-1)
		bc += add
		bc += swap
		j2 = len(bc)
		bc += jumpif
		compile2(self.arg, bc)
		patch(bc, j2, len(bc))
	def emit14(self, bc):
		bc += loadmkconst(None)
		bc += ret
	def emit15(self, bc):
		bc += loadmkconst(sowrite)
		bc += loadmkconst(self.arg)
		bc += call1
		bc += pop
	emits = emit0, emit1, emit2, emit3, emit4, emit5, emit6, emit7, emit8, emit9, emit10, emit11, emit12, emit13, emit14, emit15
	class Inst:
		__slots__ = "n", "op", "arg", "var", "sd", "si"
		def __init__(self, parent=None, op=None, arg=None):
			self.n = None
			self.op = op
			self.arg = arg
			if op is not None:
				self.var = ((),(None,),(None,None),(None,None,None))[si[op]]
				self.sd = False
			if parent:
				parent.n=self
				self.si={parent}
			else:self.si=set()
		def __str__(self, names=("ld","bin","not","pop","dup","swap","puti","putc","getc","geti","rmem","wmem","rj","jz","ret","put"),
			blut={add:"+", subtract:"-", multiply:"*", floordivide:"/", modulo:"%", cmpgt:">"}):
			return "NIL" if self.op is None else "%s\t%s\t%s"%(names[self.op],blut[self.arg] if self.op==1 else self.arg,self.var)
		def eval(self, st):return ops[self.op](self, st, *((c if c is not None else st.pop() if st else 0) for c in self.var))
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
		def emit(self, bc):return emits[self.op](self, bc)
	def compile(i,mv,tail):
		while True:
			i=mv(i)
			imv=i,mv
			if imv in pg:
				tail.n=pg[imv].n or tail
				return tail.n.si.add(tail)
			pg[imv]=tail
			pro.add(i)
			i2 = ps[i]
			if 33<=i2<=126:
				i2=b'\x10\x1d\x1f\x11\x0e\x17$$$\x0c\n\x15\x0b\x14\r\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\x12$"$ \x1a\x1e$$$$$$$$$$$$$$$$$$$$$$$$$$$\x13$!\x1c\x0f$$$$$$\x18$$$$$$$$\x19$$$$$#$$$$$\x1b$\x16'[i2-33]
				if i2<10:tail=Inst(tail, 0, i2)
				elif i2<16:tail=Inst(tail, 1, bins[i2-10])
				elif i2<25:tail=Inst(tail, i2-14)
				elif i2==36:continue
				elif i2==25:tail=Inst(tail, 11, imv)
				elif i2==26:
					tail=Inst(tail, 12)
					tail.arg=[Inst(),Inst(),Inst()]
					compile(i,mvL,tail.arg[0])
					compile(i,mvK,tail.arg[1])
					compile(i,mvH,tail.arg[2])
					mv=mvJ
				elif i2==27:
					tail=Inst(tail, 13)
					tail.arg=Inst()
					compile(i,mvJ,tail.arg)
					mv=mvK
				elif i2==28:
					tail=Inst(tail, 13)
					tail.arg=Inst()
					compile(i,mvL,tail.arg)
					mv=mvH
				elif i2==29:
					while True:
						i=mv(i)
						pro.add(i)
						i2=ps[i]
						if i2==34:break
						tail=Inst(tail, 0, i2)
				elif i2==30:return Inst(tail, 14)
				elif i2==31:i=mv(i)
				elif i2==32:mv=mvL
				elif i2==33:mv=mvK
				elif i2==34:mv=mvH
				else:mv=mvJ
	def peephole(ir, cst):
		head=ir
		while True:
			if ir.op is None:
				ir=ir.n
				continue
			if ir.sd:return head
			ir.sd=True
			op=ir.op
			if 12<=op<=14 or len(ir.si)>1:
				cst.clear()
				if 12<=op<=14:
					if op==14:return head
					elif op==13:peephole(ir.arg, [])
					else:
						for op in ir.arg:peephole(op, [])
					ir=ir.n
					continue
			if not op:
				cst.append((ir, ir.arg))
			elif op==4 and ir.n.op==3:
				ir.op = None
				ir.n.si.remove(ir)
				ir.n.n.si.add(ir)
				ir.n = ir.n.n
			elif op==4 and ir.n.op==5:
				ir.n.si.remove(ir)
				ir.n.n.si.add(ir)
				ir.n = ir.n.n
			elif cst:
				siop=si[op]
				if not siop:
					if so[op]:cst.append((ir, None))
				else:
					for cs,x in enumerate(reversed(cst), 0):
						if x[1] is None:break
					else:cs+=1
					if cs:
						if op==3:
							cst.pop()
							ir.remove()
						elif op==4:
							ai,a=cst[-1]
							ir.var=()
							ir.arg=a
							ir.op=0
							cst.append((ir, a))
						elif op==5:
							ai,a=cst.pop()
							bi,b=cst.pop()
							ai.arg=b
							bi.arg=a
							ir.remove()
							cst += (bi,a),(ai,b)
						elif op in (6,7):
							ai,a=cst.pop()
							ai.remove()
							ir.var=()
							ir.arg=("%d " if op==6 else "%c")%a
							op=ir.op=15
						elif op==13:
							ai,a=cst.pop()
							ir.op=None
							if a:ir.arg.si.remove(ir)
							else:
								ir.n.si.remove(ir)
								ir.n=ir.arg
							ir.arg=None
						else:
							a=[]
							ai=-1
							bi=-len(cst)
							for x in range(siop):
								x=ai-x
								if x<=bi+ai:a.append(None)
								else:
									c0,c1=cst[x]
									a.append(c1)
									if c1 is not None:
										del cst[x]
										ai+=1
										c0.remove()
							ir.var=a
							if op<6 and None not in a:
								x=[]
								ir.eval(x)
								ir.var=()
								ir.arg=x[0]
								op=ir.op=0
								cst.append((ir, ir.arg))
							else:cst[-siop:]=repeat((ir,None), so[op])
					else:cst[-siop:]=repeat((ir,None), so[op])
			else:cst+=repeat((ir,None), so[op])
			ir=ir.n
		return head
	def execir(ir):
		st=[]
		while True:
			while ir.op is None:ir=ir.n
			ir=ir.eval(st)
			if type(ir) is not Inst:return ir
	def compile2(ir, bc):
		while ir is not None:
			if ir.op is None:
				ir=ir.n
				continue
			if ir.sd is not True and ir.sd is not False:
				bc += jumpabs(ir.sd)
				return
			ir.sd=len(bc)
			if ir.emit(bc) is ...:return
			ir=ir.n
	empty={}
	ir=Inst()
	compile(2528,mvL,ir)
	bc=bytearray()
	while True:
		pg.clear()
		peephole(ir,[])
		bc += loadmkconst(0)
		compile2(ir, bc)
		f=FunctionType(CodeType(0,0,0,65536,0,bytes(bc),tuple(constl),(),(),"","",0,b""),empty)()
		if f is None:return
		bc.clear()
		ir=tail=Inst()
		for x in range(len(f)-1, 1, -1):tail=Inst(tail, 0, f[x])
		compile(f[0], f[1], tail)
if __name__ == "__main__":
	from sys import argv
	main(open(argv[1],"rb"))
