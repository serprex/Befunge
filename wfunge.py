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
	from opcode import opmap
	from types import CodeType,FunctionType
	from random import getrandbits
	from itertools import repeat
	from sys import stdout
	def mkemit(op):
		op = opmap[op]
		return lambda a:(144|(a&0xff00)|op<<16|(a&255)<<24).to_bytes(4,"little")
	def mkemit1(op, a):return (opmap[op]|a<<8).to_bytes(2,"little")
	swap = mkemit1("ROT_TWO",0)
	rot3 = mkemit1("ROT_THREE",0)
	pop = mkemit1("POP_TOP",0)
	dup = mkemit1("DUP_TOP",0)
	iadd = mkemit1("INPLACE_ADD",0)
	add = mkemit1("BINARY_ADD",0)
	subtract = mkemit1("BINARY_SUBTRACT",0)
	multiply = mkemit1("BINARY_MULTIPLY",0)
	floordivide = mkemit1("BINARY_FLOOR_DIVIDE",0)
	modulo = mkemit1("BINARY_MODULO",0)
	lshift = mkemit1("BINARY_LSHIFT",0)
	bor = mkemit1("BINARY_OR",0)
	subscr = mkemit1("BINARY_SUBSCR",0)
	_not = mkemit1("UNARY_NOT",0)
	ret = mkemit1("RETURN_VALUE",0)
	cmp = lambda a:mkemit1("COMPARE_OP", a)
	cmplt = cmp(0)
	cmpeq = cmp(2)
	cmpgt = cmp(4)
	cmpgte = cmp(5)
	call0 = mkemit1("CALL_FUNCTION", 0)
	call1 = mkemit1("CALL_FUNCTION", 1)
	loadconst1 = lambda a:mkemit1("LOAD_CONST", a)
	loadconst = mkemit("LOAD_CONST")
	loadmkconst = lambda a:loadconst(mkconst(a))
	jumpabs = mkemit("JUMP_ABSOLUTE")
	jump = jumpabs(0)
	jumpiforpop = mkemit("JUMP_IF_TRUE_OR_POP")(0)
	jumpifnotorpop = mkemit("JUMP_IF_FALSE_OR_POP")(0)
	jumpif = mkemit("POP_JUMP_IF_TRUE")(0)
	jumpifnot = mkemit("POP_JUMP_IF_FALSE")(0)
	def mkconst(c):
		nonlocal constl
		if c in consts:return consts[c]
		else:
			a=consts[c]=len(constl)
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
			for a in repeat(b"\x90ddd",s):r+=a
			r+=loadmkconst(s)
			compile(*imv)
			return iter(repeat(None, s)),[]
		return f
	mvL=lambda i:i-2528 if i>=2528 else i+32
	mvK=lambda i:i-1 if i&31 else i+24
	mvH=lambda i:i+2528 if i<32 else i-32
	mvJ=lambda i:i+1 if (i+1&31)<25 else i-24
	def mkop(f, *ops):
		jtbl = {}
		jidx = {}
		cs = {}
		bc = bytearray()
		bclst = []
		rval=None
		if f==1:
			jidx["-"] = len(bc)+1
			bc += jumpiforpop
			cs[len(bc)+1] = 0
			bc += b"\x90ddd"
			bc += dup
			jtbl["-"] = len(bc)
		elif f:
			jidx["-"] = len(bc)+1
			bc += jump
			jtbl["~"] = len(bc)
			cs[len(bc)+1] = 1
			bc += b"\x90ddd"
			bc += add
			cs[len(bc)+1] = 0
			bc += b"\x90ddd"
			bc += swap
			jtbl["-"] = len(bc)
			bc += dup
			cs[len(bc)+1] = f-1
			bc += b"\x90ddd"
			bc += cmpgt
			jidx["~"]=len(bc)+1
			bc += jumpifnot
		for op in ops:
			ot = type(op)
			if ot is bytes:
				bc += op
			elif ot is tuple:
				o0,o1 = op
				if o0 is None:
					cs[len(bc)+1]=o1
					bc += b"\x90ddd"
				elif o0 is ...:
					rval = o1
					break
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
					bc[j]=l>>8
					bc[j+2]=l&255
				r+=bc
				for j,l in jtbl.items():
					j=rl0+jidx[j]
					l+=rl
					r[j]=l>>8
					r[j+2]=l&255
				if comp is not None:compile(imv[0], comp)
			return rval if rval is None or rval is ... else (imv[0], rval)
		return emitop
	def mksimpleop(*ops):
		bc=bytearray()
		cs={}
		rval=None
		for op in ops:
			if type(op) is bytes:bc += op
			else:
				cs[len(bc)+1] = op
				bc += b"\x90ddd"
		def emitsimple(imv):
			nonlocal r
			for j,c in cs.items():
				c=mkconst(c)
				bc[j]=c>>8
				bc[j+2]=c&255
			r += bc
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
	op20=mkop(1, (None, -1), add, swap, (None, "%d "), swap, modulo, (None, stdout.write), swap, call1, pop)
	op21=mkop(1, (None, -1), add, swap, (None, "%c"), swap, modulo, (None, stdout.write), swap, call1, pop)
	op22=mksimpleop(1, add, getch, call0, swap)
	op23=mksimpleop(1, add, lambda:int(input()), call0, swap)
	op24=mkop(2, (None, -1), add, rot3, swap, (None, 5), lshift, bor, dup, (None, 0), cmplt, (jumpif, "a"),
		dup, (None, 2560), cmpgte, (jumpif, "b"), loadconst1(0), swap, subscr, (jump, "c"), "a", "b", _not, "c", swap)
	op25=mkop(3, (None, -3), add, rot3, swap, (None, 5), lshift, bor, dup, (None, 0), cmplt, (jumpif, "a"),
		dup, (None, 2560), cmpgte, (jumpif, "b"), dup, (None, 31), mkemit1("BINARY_AND",0), (None, 25), cmpgte, (jumpif, "c"),
		swap, rot3, dup, rot3, loadconst1(0), swap, mkemit1("STORE_SUBSCR",0),
		loadconst1(1), cmp(6), (jumpifnot, "d"), (None, None), swap, call1, mkemit1("UNPACK_SEQUENCE", 2),
		"e", mkemit1("FOR_ITER", 14), pop, rot3, swap, mkemit1("LIST_APPEND", 1), swap, (jump, "e"), ret,
		"a", "b", "c", pop, "d")
	op26=mkop(0, (None, getrandbits), (None, 2), call1, dup, (jumpifnot, "a"),
		dup, (None, 1), cmpeq, (jumpif, "b"),
		dup, (None, 2), cmpeq, (jumpif, "c"),
		pop, mvL, "a", pop, mvK, "b", pop, mvH, "c", pop, (..., mvJ))
	opIF = lambda j0,j1:mkop(1, (None, -1), add, swap, (jumpif, "a"), j0, "a", (..., j1))
	def op29(imv):
		nonlocal r
		i,mv=imv
		rl = len(r)
		while True:
			i=mv(i)
			pro.add(i)
			i2=ps[i]
			if i2==34:
				r+=loadmkconst((len(r)-rl)//6) + add
				return i,mv
			r+=loadmkconst(i2) + swap
	def op30(imv):
		nonlocal r
		r += loadmkconst(None) + ret
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
				i2=opfs[b'\x10\x1d\x1f\x11\x0e\x17$$$\x0c\n\x15\x0b\x14\r\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\x12$"$ \x1a\x1e$$$$$$$$$$$$$$$$$$$$$$$$$$$\x13$!\x1c\x0f$$$$$$\x18$$$$$$$$\x19$$$$$#$$$$$\x1b$\x16'[i2-33]](imv)
				if i2 is not None:
					if i2 is ...:return
					else:i,mv=i2
	compile(2528,mvL)
	empty={}
	skipfirst=True
	while True:
		from dis import dis
		f=FunctionType(CodeType(0,0,0,65536,0,bytes(r),tuple(constl),(),(),"","",0,b""),empty)()
		if f is None:return
		for i,f in zip(range(len(f)*4-3,0,-4),f):
			f=mkconst(f)
			r[i]=f>>8
			r[i+2]=f&255
if __name__ == "__main__":
	from sys import argv
	main(open(argv[1],"rb"))
