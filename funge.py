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
	from itertools import count,repeat
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
	mktuple = mkemit("BUILD_TUPLE")
	cmp = mkemit("COMPARE_OP")
	cmpeq = cmp(2)
	cmpgt = cmp(4)
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
			return []
		return f
	mvL=lambda i:i-2528 if i>=2528 else i+32
	mvK=lambda i:i-1 if i&31 else i+24
	mvH=lambda i:i+2528 if i<32 else i-32
	mvJ=lambda i:i+1 if (i+1&31)<25 else i-24
	def mkop(f, *ops):
		from types import FunctionType
		jtbl = {}
		jidx = {}
		cs = {}
		bc = bytearray()
		bclst = []
		rval=None
		if f==1:
			jidx["-"] = 1
			jtbl["-"] = 7
			bc += jumpiforpop
			cs[4]=0
			bc += b"ddd"
			bc += dup
		elif f:
			jidx["-"] = 1
			jtbl["-"] = 11
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
			jidx["~"]=19
			jtbl["~"]=3
			bc += jumpifnot
		for op in ops:
			if op is ...:
				rval=...
				break
			ot = type(op)
			if ot is bytes:
				bc += op
			elif ot is tuple:
				o0,o1 = op
				if o0 is None:
					cs[len(bc)+1]=o1
					bc += b"ddd"
				else:
					jidx[o1] = len(bc)+1
					bc += o0
			elif ot is str:
				jtbl[op] = len(bc)
			else:
				bclst += (bc, jtbl, cs, op),
				bc = bytearray()
				jtbl = {}
				cs = {}
		bclst += (bc, jtbl, cs, None),
		def emitop(imv):
			nonlocal r
			rl0=None
			for a in bclst:
				rl=len(r)
				if rl0 is None:rl0=rl
				bc,jtbl,cs,comp = a
				for j,l in cs.items():
					l=mkconst(wmem(imv) if l is None else l)
					bc[j]=l[0]
					bc[j+1]=l[1]
				r+=bc
				for j,l in jtbl.items():
					j=rl0+jidx[j]
					l+=rl
					r[j]=l&255
					r[j+1]=l>>8
				if comp is not None:compile(imv[0], comp)
			return rval
		return emitop
	def mksimpleop(*ops):
		bc=bytearray()
		cs={}
		rval=None
		for op in ops:
			if op is ...:
				rval = ...
				break
			elif type(op) is bytes:bc += op
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
			return rval
		return emitsimple
	opC=lambda op:mksimpleop(1, add, op, swap)
	binOp=lambda bin:mkop(2, (None, -1), add, rot3, bin, swap)
	op10=binOp(add)
	op11=binOp(subtract)
	op12=binOp(multiply)
	op13=binOp(floordivide)
	op14=binOp(modulo)
	op15=mkop(2, (None, -1), add, rot3, cmpgt, swap)
	op16=mkop(1, swap, _not, swap)
	op17=mkop(0, dup, (jumpifnot, "a"), (None, -1), add, swap, pop, "a")
	op18=mkop(1, (None, 1), add, swap, dup, rot3, rot3)
	op19=mkop(2, rot3, swap, rot3, rot3)
	op20=mkop(1, (None, -1), add, swap, (None, lambda x:print(+x,end=' ')), swap, call1, pop)
	op21=mkop(1, (None, -1), add, swap, (None, "%c"), swap, modulo, (None, stdout.write), swap, call1, pop)
	op22=mksimpleop(1, add, getch, call0, swap)
	op23=mksimpleop(1, add, lambda:int(input()), call0, swap)
	op24=mkop(2, (None, -1), add, rot3, swap, (None, 5), lshift, bor, dup, (None, 0), cmp(0), (jumpif, "a"),
		dup, (None, 2560), cmp(5), (jumpif, "b"), loadconst(0), swap, subscr, (jump, "c"), "a", "b", _not, "c", swap)
	op25=mkop(3, (None, -3), add, rot3, swap, (None, 5), lshift, bor, dup, (None, 0), cmp(0), (jumpif, "a"),
		dup, (None, 2560), cmp(5), (jumpif, "b"), dup, (None, 31), mkemit("BINARY_AND"), (None, 25), cmp(5), (jumpif, "c"),
		swap, rot3, dup, rot3, loadconst(0), swap, mkemit("STORE_SUBSCR"),
		loadconst(1), cmp(6), (jumpifnot, "d"), dup, (None, None), swap, call1, swap, "e", dup,
		(jumpifnot, "f"), rot3, swap, mktuple(1), iadd, swap, (None, -1), add, (jump, "e"),
		"f", pop, ret, "a", "b", "c", pop, "d")
	op26=mkop(0, (None, getrandbits), (None, 2), call1, dup, (jumpifnot, "a"),
		dup, (None, 1), cmpeq, (jumpif, "b"),
		dup, (None, 2), cmpeq, (jumpif, "c"),
		pop, mvL, "a", pop, mvK, "b", pop, mvH, "c", pop, mvJ, ...)
	opIF = lambda j0,j1:mkop(1, (None, -1), add, swap, (jumpif, "a"), j0, "a", j1, ...)
	def op29(imv):
		nonlocal r
		i,mv=imv
		for n in count():
			i=mv(i)
			pro.add(i)
			i2=ps[i]
			if i2==34:
				r+=loadmkconst(n)
				r+=add
				return i,mv
			r+=loadmkconst(i2)
			r+=swap
	op30=mksimpleop(None, ret, ...)
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
				i2=opfs[b'\x10\x1d\x1f\x11\x0e\x17$$$\x0c\n\x15\x0b\x14\r\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\x12$"$ \x1a\x1e$$$$$$$$$$$$$$$$$$$$$$$$$$$\x13$!\x1c\x0f$$$$$$\x18$$$$$$$$\x19$$$$$#$$$$$\x1b$\x16'[i2-33]](imv)
				if i2 is not None:
					if i2 is ...:return
					else:i,mv=i2
	compile(2528,mvL)
	empty={}
	while True:
		f=FunctionType(CodeType(0,0,0,65536,0,bytes(r),tuple(constl),(),(),"","",0,b""),empty)()
		if f is None:return
		for i,f in zip(range(len(f)*3-2,0,-3),f):
			f=mkconst(f)
			r[i]=f[0]
			r[i+1]=f[1]
if __name__ == "__main__":
	from sys import argv
	main(open(argv[1],"rb"))
