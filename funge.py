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
	subscr = mkemit("BINARY_SUBSCR")
	_not = mkemit("UNARY_NOT")
	ret = mkemit("RETURN_VALUE")
	cmp = mkemit("COMPARE_OP")
	cmplt = cmp(0)
	cmpeq = cmp(2)
	cmpgt = cmp(4)
	cmpgte = cmp(5)
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
	r=bytearray(loadmkconst(0))
	def wmem(imv):
		def f(s):
			nonlocal r
			consts.clear()
			constl[2:]=()
			pro.clear()
			pg.clear()
			r.clear()
			for a in repeat(b"ddd",s):r+=a
			r+=loadmkconst(s)
			compile(*imv)
			return iter(repeat(s, s)),[]
		return f
	mvL=lambda i:i-2528 if i>=2528 else i+32
	mvK=lambda i:i-1 if i&31 else i+24
	mvH=lambda i:i+2528 if i<32 else i-32
	mvJ=lambda i:i+1 if (i&31)<24 else i-24
	def mkop(f, *ops):
		jtbl = {}
		jpad = {}
		cs = {}
		bc = bytearray()
		if f==1:
			jtbl[1]=9
			bc += jumpiforpop
			cs[4]=0
			cs[7]=1
			bc += b"dddddd"
		elif f:
			jtbl[1]=11
			bc += jump
			cs[4]=1
			bc += b"ddd"
			bc += add
			cs[8]=0
			bc += b"ddd"
			bc += swap
			bc += dup
			cs[13]=f-1
			bc += b"ddd"
			bc += cmpgt
			jtbl[19]=3
			bc += jumpifnot
		for op in ops:
			ot = type(op)
			if ot is bytes:
				bc += op
			elif ot is tuple:
				o0,o1 = op
				if o0 is None:
					cs[len(bc)+1]=o1
					bc += b"ddd"
				else:
					if o1 in jpad:
						jtbl[len(bc)+1]=jpad[o1]
					else:
						jpad[o1]=len(bc)+1
					bc += o0
			elif op in jpad:
				jtbl[jpad[op]]=len(bc)
			else:
				jpad[op]=len(bc)
		def emitop(imv):
			nonlocal r
			for j,l in cs.items():
				l=mkconst(wmem(imv) if l is None else l)
				bc[j]=l[0]
				bc[j+1]=l[1]
			rl=len(r)
			r+=bc
			for j,l in jtbl.items():
				j+=rl
				l+=rl
				r[j]=l&255
				r[j+1]=l>>8
		return emitop
	def mksimpleop(*ops):
		bc=bytearray()
		cs={}
		for op in ops:
			if type(op) is bytes:bc += op
			else:
				cs[len(bc)+1] = op
				bc += b"ddd"
		def emitsimple(imv):
			nonlocal r
			for j,c in cs.items():
				c=mkconst(c)
				bc[j]=c[0]
				bc[j+1]=c[1]
			r += bc
		return emitsimple
	opC=lambda op:mksimpleop(1, add, op, swap)
	binOp=lambda bin:mkop(2, (None, -1), add, rot3, bin, swap)
	op10=binOp(add)
	op11=binOp(subtract)
	op12=binOp(multiply)
	op13=binOp(floordivide)
	op14=binOp(modulo)
	op15=binOp(cmpgt)
	op16=mkop(1, swap, _not, swap)
	op17=mkop(0, dup, (jumpifnot, "a"), (None, -1), add, swap, pop, "a")
	op18=mkop(1, (None, 1), add, swap, dup, rot3, swap)
	op19=mkop(2, rot3, swap, rot3, rot3)
	op20=mkop(1, (None, -1), add, swap, (None, "%d "), swap, modulo, (None, stdout.write), swap, call1, pop)
	op21=mkop(1, (None, -1), add, swap, (None, "%c"), swap, modulo, (None, stdout.write), swap, call1, pop)
	op22=mksimpleop(1, add, getch, call0, swap)
	op23=mksimpleop(1, add, lambda:int(input()), call0, swap)
	op24=mkop(2, (None, -1), add, rot3, swap, (None, 5), lshift, bor, dup, (None, 0), cmplt, (jumpif, "a"),
		dup, (None, 2560), cmpgte, (jumpif, "b"), loadconst(0), swap, subscr, (jump, "c"), "a", "b", _not, "c", swap)
	op25=mkop(3, (None, -3), add, rot3, swap, (None, 5), lshift, bor, dup, (None, 0), cmplt, (jumpif, "a"),
		dup, (None, 2560), cmpgte, (jumpif, "b"), dup, (None, 31), mkemit("BINARY_AND"), (None, 25), cmpgte, (jumpif, "c"),
		swap, rot3, dup, rot3, loadconst(0), swap, mkemit("STORE_SUBSCR"),
		loadconst(1), cmp(6), (jumpifnot, "d"), (None, None), swap, call1, mkemit("UNPACK_SEQUENCE")(2),
		"e", mkemit("FOR_ITER")(10), pop, rot3, swap, mkemit("LIST_APPEND")(1), swap, (jump, "e"), ret,
		"a", "b", "c", pop, "d")
	def op26(imv):
		nonlocal r
		imv=imv[0]
		r+=loadmkconst(getrandbits)
		r+=loadmkconst(2)
		r+=call1
		r+=dup
		ja=len(r)+1
		r+=jumpifnot
		r+=dup
		r+=loadmkconst(1)
		r+=cmpeq
		jb=len(r)+1
		r+=jumpif
		r+=dup
		r+=loadmkconst(2)
		r+=cmpeq
		jc=len(r)+1
		r+=jumpif
		r+=pop
		compile(imv,mvL)
		r[ja],r[ja+1]=len(r).to_bytes(2,"little")
		r+=pop
		compile(imv,mvK)
		r[jb],r[jb+1]=len(r).to_bytes(2,"little")
		r+=pop
		compile(imv,mvH)
		r[jc],r[jc+1]=len(r).to_bytes(2,"little")
		r+=pop
		return imv,mvJ
	def opIF(j0,j1):
		def f(imv):
			nonlocal r
			imv=imv[0]
			jsp=len(r)+1
			r+=jumpiforpop
			r+=loadmkconst(0)
			jb=len(r)+1
			r+=jump
			r[jsp],r[jsp+1]=len(r).to_bytes(2,"little")
			r+=loadmkconst(-1)
			r+=add
			r+=swap
			ja=len(r)+1
			r+=jumpif
			r[jb],r[jb+1]=len(r).to_bytes(2,"little")
			compile(imv,j0)
			r[ja],r[ja+1]=len(r).to_bytes(2,"little")
			return imv,j1
		return f
	def op29(imv):
		nonlocal r
		i,mv=imv
		rl = len(r)
		while True:
			i=mv(i)
			pro.add(i)
			i2=ps[i]
			if i2==34:
				r+=loadmkconst(len(r)-rl>>2)
				r+=add
				return i,mv
			r+=loadmkconst(i2)
			r+=swap
	def op30(imv):
		nonlocal r
		r+=loadmkconst(None)
		r+=ret
		return ...
	def op31(imv):
		i,mv=imv
		return mv(i),mv
	opDIR=lambda d:lambda imv:(imv[0],d)
	opfs=list(map(opC, range(10)))
	opfs+=(op10,op11,op12,op13,op14,op15,op16,op17,op18,op19,op20,op21,op22,op23,op24,op25,op26,opIF(mvJ,mvK),opIF(mvL,mvH),op29,op30,op31,opDIR(mvL),opDIR(mvK),opDIR(mvH),opDIR(mvJ),lambda imv:None)
	def compile(i,mv):
		nonlocal r
		while True:
			i=mv(i)
			imv=i,mv
			if imv in pg:
				r+=jumpabs(pg[imv])
				return
			pg[imv]=len(r)
			pro.add(i)
			i2 = ps[i]
			if 33<=i2<=126:
				i2=opfs[b'\x10\x1d\x1f\x11\x0e\x17$$$\x0c\n\x15\x0b\x14\r\0\1\2\3\4\5\6\7\x08\t\x12$"$ \x1a\x1e$$$$$$$$$$$$$$$$$$$$$$$$$$$\x13$!\x1c\x0f$$$$$$\x18$$$$$$$$\x19$$$$$#$$$$$\x1b$\x16'[i2-33]](imv)
				if i2 is not None:
					if i2 is ...:return
					else:i,mv=i2
	compile(2528,mvL)
	empty={}
	while True:
		f=FunctionType(CodeType(0,0,0,65536,0,bytes(r),(*constl,),(),(),"","",0,b""),empty)()
		if f is None:return
		for i,f in zip(range(len(f)*3-2,0,-3),f):
			f=mkconst(f)
			r[i]=f[0]
			r[i+1]=f[1]
if __name__ == "__main__":
	from sys import argv
	main(open(argv[1],"rb"))
