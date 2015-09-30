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

def main(pstring, argv=()):
	from opcode import opmap,HAVE_ARGUMENT,hasjabs
	from types import CodeType,FunctionType
	from random import randint
	from sys import stdout
	hasjabs = frozenset(hasjabs)
	ps = [0]*2560
	if debug:print(pstring)
	pstring = pstring.split("\n")
	for y,line in enumerate(pstring):
		if y>25:break
		for x,c in enumerate(line):
			if x>80:break
			ps[x<<5|y]=ord(c)
	r=pro=pg=None
	def initstate():
		nonlocal pg,pro,r
		r=bytearray()
		pro=bytearray(b"\0")*640
		pg=[None]*10240
	initstate()
	def rmem(x,y):return ps[x<<5|y] if 0<=x<=80 and 0<=y<=25 else 0
	def wmem(x,y,v,i,s):
		if 0<=x<=80 and 0<=y<=25:
			y|=x<<5
			ps[y]=v
			if getpro(y):
				initstate()
				r.extend(b"d"*(s*3))
				compile(i,s)
				return True
			return False
	def rng():return randint(0,3)
	def getop(i):return b'\x10\x1d\x1f\x11\x0e\x17$$$\x0c\n\x15\x0b\x14\r\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\x12$"$ \x1a\x1e$$$$$$$$$$$$$$$$$$$$$$$$$$$\x13$!\x1c\x0f$$$$$$\x18$$$$$$$$\x19$$$$$#$$$$$\x1b$\x16'[i-33] if 33<=i<=126 else 36
	def emit(op,arg=None):
		r.append(opmap[op])
		if arg is not None:emitarg(arg)
	def mkemit(op):
		op = opmap[op]
		def f(arg=None):
			if (arg is None) != (op<HAVE_ARGUMENT):print("HAVE_ARGUMENT mismatch", op)
			if arg is None:r.append(op)
			else:r.extend((op,arg&255,arg>>8))	
		return f
	swap = mkemit("ROT_TWO")
	rot3 = mkemit("ROT_THREE")
	pop = mkemit("POP_TOP")
	dup = mkemit("DUP_TOP")
	call = mkemit("CALL_FUNCTION")
	jump = mkemit("JUMP_ABSOLUTE")
	def popcall(arg):
		call(arg)
		pop()
	def patch(loc,off):
		r[loc+1]=off&255
		r[loc+2]=off>>8
	consts = []
	def emitidx(a,c):
		if c in a:
			emitarg(a.index(c))
		else:
			emitarg(len(a))
			a.append(c)
	def loadconst(c):
		r.append(100)
		emitidx(consts, c)
	putch = stdout.write
	putint = lambda x:print(+x,end=' ')
	def storefast(x):
		r.append(125)
		emitarg(x)
	def loadfast(x):
		r.append(124)
		emitarg(x)
	def emitarg(arg):
		r.extend((arg&255,arg>>8))
	def incrsp(n):
		if n:
			loadfast(0)
			loadconst(n)
			emit("BINARY_ADD")
			storefast(0)
	def prbug(x, oneline=False):
		if not debug:return
		loadconst(print)
		loadconst(x)
		if oneline:
			loadconst("end")
			loadconst(" ")
			loadconst("flush")
			loadconst(True)
		popcall(513 if oneline else 1)
	def debugtop(x=""):
		if not debug:return
		loadfast(0)
		loadconst(print)
		swap()
		loadconst(str(x)+"?")
		call(2)
		pop()
		emit("DUP_TOP_TWO")
		loadconst(print)
		rot3()
		loadfast(0)
		loadconst(str(x)+"!")
		call(4)
		pop()
	def spguard(f,n=0):
		if f == 1:
			loadfast(0)
			emit("POP_JUMP_IF_TRUE",len(r)+12)
			loadconst(1)
			storefast(0)
			loadconst(0)
			incrsp(n)
		elif f == 2:
			loadfast(0)
			loadconst(1)
			emit("DUP_TOP_TWO")
			emit("COMPARE_OP",4)
			f=len(r)
			emit("POP_JUMP_IF_TRUE",0)
			emit("COMPARE_OP",2)
			emit("POP_JUMP_IF_TRUE",len(r)+6)
			loadconst(0)
			loadconst(0)
			loadconst(2+n)
			storefast(0)
			j=len(r)
			jump(0)
			patch(f,len(r))
			pop()
			pop()
			incrsp(n)
			patch(j,len(r))
		elif f:
			loadfast(0)
			i=len(r)
			jump(0)
			loadconst(0)
			loadfast(0)
			loadconst(1)
			emit("BINARY_ADD")
			dup()
			storefast(0)
			patch(i,len(r))
			loadconst(f-1)
			emit("COMPARE_OP",4)
			emit("POP_JUMP_IF_FALSE",i+3)
			incrsp(n)
	def mv(i):
		i3=i&3
		return (
			(i-10112 if i>=10112 else i+128) if i3==0 else
			(i-4 if i&124 else i+96) if i3==1 else
			(i+10112 if i<128 else i-128) if i3==2 else
			(i+4 if (i+4&124)<100 else i-96))
	def setpro(i):pro[i>>4]|=1<<(i>>1&6)
	def getpro(i):return pro[i>>4]&(1<<(i>>1&6))
	def opC(op,i):
		incrsp(1)
		loadconst(op)
	def binOp(name):
		def g(op,i):
			prbug("\t"+name,True)
			spguard(2,-1)
			emit(name)
			prbug("done")
		return g
	op10=binOp("BINARY_ADD")
	op11=binOp("BINARY_SUBTRACT")
	op12=binOp("BINARY_MULTIPLY")
	op13=binOp("BINARY_FLOOR_DIVIDE")
	op14=binOp("BINARY_MODULO")
	def op15(op,i):
		spguard(2,-1)
		emit("COMPARE_OP",4)
	def op16(op,i):
		spguard(1)
		emit("UNARY_NOT")
	def op17(op,i):
		loadfast(0)
		i=len(r)
		emit("POP_JUMP_IF_FALSE",0)
		incrsp(-1)
		pop()
		patch(i,len(r))
	def op18(op,i):
		spguard(1,1)
		dup()
	def op19(op,i):
		spguard(2)
		swap()
	def op20(op,i):
		spguard(1,-1)
		loadconst(putint)
		swap()
		popcall(1)
	def op21(op,i):
		spguard(1,-1)
		loadconst("%c")
		swap()
		emit("BINARY_MODULO")
		loadconst(putch)
		swap()
		popcall(1)
	def op22(op,i):
		incrsp(1)
		loadconst(getch)
		call(0)
	def op23(op,i):
		incrsp(1)
		loadconst(int)
		loadconst(input)
		call(0)
		call(1)
	def op24(op,i):
		spguard(2,-1)
		loadconst(rmem)
		rot3()
		call(2)
	def op25(op,i):
		spguard(3,-3)
		storefast(1)
		loadconst(wmem)
		rot3()
		loadfast(1)
		loadconst(i)
		loadfast(0)
		call(5)
		j=len(r)
		emit("POP_JUMP_IF_FALSE", 0)
		emit("BUILD_LIST",0)
		loadfast(0)
		dup()
		j2=len(r)
		emit("POP_JUMP_IF_FALSE",0)
		rot3()
		swap()
		emit("BUILD_TUPLE",1)
		emit("INPLACE_ADD")
		swap()
		loadconst(1)
		emit("BINARY_SUBTRACT")
		emit("JUMP_ABSOLUTE",j2-1)
		pop()
		emit("RETURN_VALUE")
		i=len(r)
		patch(j,i)
		patch(j2,i-2)
	def op26(op,i):
		loadconst(rng)
		call(0)
		dup()
		offsets = [len(r)]
		emit("POP_JUMP_IF_FALSE",0)
		for a in 1,2:
			dup()
			loadconst(a)
			emit("COMPARE_OP",2)
			offsets.append(len(r))
			emit("POP_JUMP_IF_TRUE",0)
		for a in range(4):
			if a:patch(offsets[a-1],len(r))
			compile(i&~3|a,True)
		return -1
	def opIF(op,i):
		spguard(1,-1)
		j = len(r)
		emit("POP_JUMP_IF_TRUE",0)
		for a in range(2):
			if a==1:patch(j,len(r))
			compile(i&~3|(3-a*2 if op==27 else a*2))
		return -1
	def op29(op,i):
		i=mv(i)
		n=0
		while ps[i>>2]!=34:
			loadconst(ps[i>>2])
			i=mv(i)
			n+=1
		incrsp(n)
		return i
	def op30(op,i):
		loadconst(0)
		emit("RETURN_VALUE")
		return -1
	def op31(op,i):return mv(i)
	def opDIR(op,i):return i&~3|op&3
	def op36(op,i):pass
	opfs = (opC,opC,opC,opC,opC,opC,opC,opC,opC,opC,op10,op11,op12,
		op13,op14,op15,op16,op17,op18,op19,op20,op21,op22,op23,op24,
		op25,op26,opIF,opIF,op29,op30,op31,opDIR,opDIR,opDIR,opDIR,op36)
	def compile(i, popflag=False):
		if popflag is True:pop()
		elif popflag is not False:
			loadconst(popflag)
			storefast(0)
		i=mv(i)
		while True:
			if pg[i] is not None:
				prbug("JUMP"+str(pg[i]))
				jump(pg[i])
				return
			pg[i]=len(r)
			op = getop(ps[i>>2])
			setpro(i)
			if op < 31 and debug==3:
				loadconst(print)
				loadfast(0)
				loadconst(op)
				popcall(2)
			ni=opfs[op](op,i)
			if ni is not None:
				if ni == -1:return
				else:i=ni
			i=mv(i)
	def filterempty(r):
		i=0
		while i<len(r):
			op = r[i]
			n = i+(1 if op<HAVE_ARGUMENT else 3)
			while i<n:
				if op:yield r[i]
				i+=1
		return r
	def optimize(r):
		if "-o" in argv:return r
		from collections import defaultdict
		jtbl=defaultdict(list)
		i=0
		jabs=113
		while i<len(r):
			op = r[i]
			if op in hasjabs:
				jtbl[r[i+1]|r[i+2]<<8].append(i)
			i+=1 if op<HAVE_ARGUMENT else 3
		return filterempty(r)
	compile(10112,0)
	def stackfix(a):
		for i,a in zip(range(len(a)*3-2,0,-3),a):
			if a in consts:a=consts.index(a)
			else:
				consts.append(a)
				a=len(consts)-1
			r[i]=a&255
			r[i+1]=a>>8
	def prog():
		do=True
		while do != 0:
			if do is not True:stackfix(do)
			f=FunctionType(CodeType(0,0,2,65536,0,bytes(optimize(r)),tuple(consts),(),("s","t"),"","",0,b""),{})
			if debug>1 or "dis" in argv:
				from dis import dis
				dis(f)
			do=f()
			if debug:print(do)
	return prog
if __name__ == "__main__":
	from sys import argv
	debug = argv.count("d")
	main(open(argv[1]).read(),argv)()
