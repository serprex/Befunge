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

def main(pro, argv=()):
	from opcode import opmap,HAVE_ARGUMENT
	from types import CodeType,FunctionType
	from random import getrandbits
	from sys import stdout
	putint = lambda x:print(+x,end=' ')
	ps = [0]*2560
	for y,line in enumerate(pro):
		if y>=25:break
		for x,c in enumerate(line):
			if x>=80:break
			ps[x<<5|y]=c
	pg={}
	consts={}
	constl=[ps]
	pro=set()
	r=bytearray()
	def wmem(i):
		def f(x):
			v,x,y,s=x
			y|=x<<5
			if (y&31)<25 and 0<=y<2560:
				ps[y]=v
				if y in pro:
					r[:]=b"d"*(s*3)
					consts.clear()
					constl[1:]=()
					pro.clear()
					pg.clear()
					loadconst(mkconst(s))(r)
					return compile(i)
			return False
		return f
	def mkemit(op):
		op = opmap[op]
		return (lambda r:r.append(op)) if op<HAVE_ARGUMENT else (lambda a:lambda r:r.extend((op,a&255,a>>8)))
	swap = mkemit("ROT_TWO")
	rot3 = mkemit("ROT_THREE")
	pop = mkemit("POP_TOP")
	dup = mkemit("DUP_TOP")
	call = mkemit("CALL_FUNCTION")
	iadd = mkemit("INPLACE_ADD")
	add = mkemit("BINARY_ADD")
	subtract = mkemit("BINARY_SUBTRACT")
	multiply = mkemit("BINARY_MULTIPLY")
	floordivide = mkemit("BINARY_FLOOR_DIVIDE")
	modulo = mkemit("BINARY_MODULO")
	lshift = mkemit("BINARY_LSHIFT")
	bor = mkemit("BINARY_OR")
	subscr = mkemit("BINARY_SUBSCR")
	mktuple = mkemit("BUILD_TUPLE")
	mklist = mkemit("BUILD_LIST")
	_not = mkemit("UNARY_NOT")
	cmp = mkemit("COMPARE_OP")
	jumpabs = mkemit("JUMP_ABSOLUTE")
	jump = bytes((opmap["JUMP_ABSOLUTE"],0,0))
	jumpiforpop = bytes((opmap["JUMP_IF_TRUE_OR_POP"],0,0))
	jumpifnotorpop = bytes((opmap["JUMP_IF_FALSE_OR_POP"],0,0))
	jumpif = bytes((opmap["POP_JUMP_IF_TRUE"],0,0))
	jumpifnot = bytes((opmap["POP_JUMP_IF_FALSE"],0,0))
	ret = mkemit("RETURN_VALUE")
	loadconst = mkemit("LOAD_CONST")
	def mkconst(c):
		nonlocal constl
		k = (c, type(c))
		if k in consts:a=consts[k]
		else:
			a=consts[k]=len(constl)
			constl += c,
		return a
	def mv(i):
		i3=i&3
		return (
			(i-10112 if i>=10112 else i+128) if i3==0 else
			(i-4 if i&124 else i+96) if i3==1 else
			(i+10112 if i<128 else i-128) if i3==2 else
			(i+4 if (i+4&124)<100 else i-96))
	def mkop(f, n, *ops):
		from types import FunctionType
		jtbl = {}
		jidx = {}
		cs = {}
		bc = bytearray()
		bclst = []
		wmemloc = None
		rval=None
		if f==1:
			jidx["-"] = 1
			jtbl["-"] = 7
			bc += jumpiforpop
			cs[4]=0
			bc += b"ddd"
			dup(bc)
		elif f:
			jidx["-"] = 1
			jtbl["-"] = 11
			bc += jump
			cs[len(bc)+1]=1
			bc += b"ddd"
			add(bc)
			cs[len(bc)+1]=0
			bc += b"ddd"
			swap(bc)
			dup(bc)
			cs[len(bc)+1]=f-1
			bc += b"ddd"
			cmp(4)(bc)
			jidx["~"]=len(bc)+1
			jtbl["~"]=3
			bc += jumpifnot
		if n:
			cs[len(bc)+1]=n
			bc += b"ddd"
			add(bc)
		for op in ops:
			if op is None:
				wmemloc = len(bc)+1
				bc += b"ddd"
			elif op is ...:
				rval=-1
				break
			ot = type(op)
			if ot is FunctionType:
				op(bc)
			elif ot is bytearray:
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
			elif ot is int:
				bclst += (bc, jtbl, cs, op, wmemloc),
				bc = bytearray()
				jtbl = {}
				cs = {}
				wmemloc = None
		bclst += (bc, jtbl, cs, None, wmemloc),
		def emitop(i):
			nonlocal r
			rl0=len(r)
			rl01=rl0+1
			for a in bclst:
				bc,jtbl,cs,comp,wm = a
				rl=len(r)
				rl1=rl+1
				r+=bc
				for j,l in jtbl.items():
					j=jidx[j]
					r[rl0+j]=rl+l&255
					r[rl01+j]=rl+l>>8
				for j,c in cs.items():
					l=mkconst(c)
					r[rl+j]=l&255
					r[rl1+j]=l>>8
				if wm is not None:
					l=mkconst(wmem(i))
					r[rl+wm]=l&255
					r[rl1+wm]=l>>8
				if comp is not None:compile(i&~3|comp)
			return rval
		return emitop
	opC=lambda op:mkop(0, 0, (None, 1), add, (None, op), swap)
	binOp=lambda bin:mkop(2,-1, rot3, bin, swap)
	op10=binOp(add)
	op11=binOp(subtract)
	op12=binOp(multiply)
	op13=binOp(floordivide)
	op14=binOp(modulo)
	op15=mkop(2,-1, rot3, cmp(4), swap)
	op16=mkop(1, 0, swap, _not, swap)
	op17=mkop(0, 0, dup, (jumpifnot, "a"), (None, -1), add, swap, pop, "a")
	op18=mkop(1, 1, swap, dup, rot3, rot3)
	op19=mkop(2, 0, rot3, swap, rot3, rot3)
	op20=mkop(1,-1, swap, (None, putint), swap, call(1), pop)
	op21=mkop(1,-1, swap, (None, "%c"), swap, modulo, (None, stdout.write), swap, call(1), pop)
	op22=mkop(0, 0, (None, 1), add, (None, getch), call(0), swap)
	op23=mkop(0, 0, (None, 1), add, (None, int), (None, input), call(0), call(1), swap)
	op24=mkop(2,-1, rot3, swap, (None, 5), lshift, bor, dup, (None, 0), cmp(0), (jumpif, "a"),
		dup, (None, 2560), cmp(5), (jumpif, "b"), loadconst(0), swap, subscr, (jump, "c"), "a", "b", _not, "c", swap)
	op25=mkop(3,-3, mktuple(4), dup, (None, 3), subscr, swap, None, swap, call(1), (jumpifnot, "a"), mktuple(0), swap, "c", dup, (jumpifnot, "b"),
		rot3, swap, mktuple(1), iadd, swap, (None, 1), subtract, (jump, "c"), "b", pop, ret, "a")
	op26=mkop(0, 0, (None, getrandbits), (None, 2), call(1), dup, (jumpifnot, "a"),
		dup, (None, 1), cmp(2), (jumpif, "b"),
		dup, (None, 2), cmp(2), (jumpif, "c"),
		pop, 0, "a", pop, 1, "b", pop, 2, "c", pop, 3, ...)
	opIF = lambda j0,j1:mkop(1,-1, swap, (jumpif, "a"), j0, "a", j1, ...)
	def op29(i):
		n=0
		while True:
			i=mv(i)
			i2=i>>2
			pro.add(i2)
			op=ps[i2]
			if op==34:
				loadconst(mkconst(n))(r)
				add(r)
				return i
			loadconst(mkconst(op))(r)
			swap(r)
			n+=1
	op30=mkop(0, 0, (None, True), ret, ...)
	def opDIR(d):return lambda i:i&~3|d
	opfs=list(map(opC, range(10)))
	opfs+=(op10,op11,op12,op13,op14,op15,op16,op17,op18,op19,op20,op21,op22,op23,op24,op25,op26,opIF(3,1),opIF(0,2),op29,op30,mv,opDIR(0),opDIR(1),opDIR(2),opDIR(3),(lambda i:None))
	def compile(i):
		while True:
			i=mv(i)
			if i in pg:return not jumpabs(pg[i])(r)
			pg[i]=len(r)
			i2 = i>>2
			pro.add(i2)
			i2 = ps[i2]
			if 33<=i2<=126:
				i2=opfs[b'\x10\x1d\x1f\x11\x0e\x17$$$\x0c\n\x15\x0b\x14\r\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\x12$"$ \x1a\x1e$$$$$$$$$$$$$$$$$$$$$$$$$$$\x13$!\x1c\x0f$$$$$$\x18$$$$$$$$\x19$$$$$#$$$$$\x1b$\x16'[i2-33]](i)
				if i2 is not None:
					if i2 == -1:return True
					else:i=i2
	loadconst(mkconst(0))(r)
	compile(10112)
	empty={}
	while True:
		f=FunctionType(CodeType(0,0,0,65536,0,bytes(r),tuple(constl),(),(),"","",0,b""),empty)()
		if f is True:return
		for i,f in zip(range(len(f)*3-2,0,-3),f):
			f=mkconst(f)
			r[i]=f&255
			r[i+1]=f>>8
if __name__ == "__main__":
	from sys import argv
	main(open(argv[1],"rb"),argv)
