#!/bin/python
from sys import stdout
def getch():
	try:import termios
	except ImportError:
		from msvcrt import getch
		return lambda:ord(getch())
	from sys import stdin
	def getch():
		fd=stdin.fileno()
		oldset=termios.tcgetattr(fd)
		newset=oldset[:]
		try:
			newset[3]&=-11
			termios.tcsetattr(fd, termios.TCSANOW, newset)
			return ord(stdin.read(1))
		finally:termios.tcsetattr(fd, termios.TCSANOW, oldset)
	return getch
getch = getch()

def main(pstring, pop=0):
	from opcode import opmap
	from types import CodeType,FunctionType
	from random import randint
	ps = [0]*2560
	print(pstring)
	pstring = pstring.split("\n")
	for y,line in enumerate(pstring):
		if y>25:break
		for x,c in enumerate(line):
			if x>80:break
			ps[x<<5|y]=ord(c)
	pg = [-1]*10240
	def rmem(x,y):return ps[x<<5|y] if 0<=x<=80 and 0<=y<=25 else 0
	def wmem(x,y,v):
		nonlocal r
		if 0<=x<=80 and 0<=25<=y:
			y|=x<<5
			ps[y]=v
			if getpro(y):
				r=bytearray()
				compile(i)
				return True
		return False
	def rng():return randint(0,3)
	pro = bytearray((0,))*640
	r = bytearray()
	def getop(i):return b'\x10\x1d\x1f\x11\x0e\x17$$$\x0c\n\x15\x0b\x14\r\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\x12$"$ \x1a\x1e$$$$$$$$$$$$$$$$$$$$$$$$$$$\x13$!\x1c\x0f$$$$$$\x18$$$$$$$$\x19$$$$$#$$$$$\x1b$\x16'[i-33] if 33<=i<=126 else 36
	def emit(op):r.append(opmap[op])
	def patch(locs,offs):
		for x,a in zip(locs,offs):
			r[x+1]=a&255
			r[x+2]=a>>8
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
	def storefast(x):
		r.append(125)
		emitarg(x)
	def loadfast(x):
		r.append(124)
		emitarg(x)
	def emitoparg(op,arg):
		emit(op)
		emitarg(arg)
	def emitarg(arg):
		r.extend((arg&255,arg>>8))
	def incrsp(n):
		if n:
			loadfast(0)
			loadconst(n)
			emit("BINARY_ADD")
			storefast(0)
	def spguard(f,n=0):
		if f:
			loadfast(0)
			i=len(r)
			emitoparg("JUMP_ABSOLUTE",0)
			loadfast(0)
			loadconst(1)
			emit("BINARY_ADD")
			emit("DUP_TOP")
			storefast(0)
			patch((i,),(len(r),))
			loadconst(f-1)
			emitoparg("COMPARE_OP",4)
			emitoparg("POP_JUMP_IF_FALSE",i+3)
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
			spguard(2,-1)
			emit(name)
		return g
	op10=binOp("BINARY_ADD")
	op11=binOp("BINARY_SUBTRACT")
	op12=binOp("BINARY_MULTIPLY")
	op13=binOp("BINARY_FLOOR_DIVIDE")
	op14=binOp("BINARY_MODULO")
	def op15(op,i):
		spguard(2,-1)
		emitoparg("COMPARE_OP",4)
	def op16(op,i):
		spguard(1)
		emit("UNARY_NOT")
	def op17(op,i):
		spguard(1,-1)
		emit("POP_TOP")
	def op18(op,i):
		incrsp(1)
		emit("DUP_TOP")
	def op19(op,i):
		spguard(2)
		emit("ROT_TWO")
	def op20(op,i):
		spguard(1,-1)
		emit("UNARY_POSITIVE")
		loadconst(print)
		emit("ROT_TWO")
		emitoparg("CALL_FUNCTION",1)
		emit("POP_TOP")
	def op21(op,i):
		spguard(1,-1)
		loadconst(chr)
		emit("ROT_TWO")
		emitoparg("CALL_FUNCTION",1)
		loadconst(putch)
		emit("ROT_TWO")
		emitoparg("CALL_FUNCTION",1)
		emit("POP_TOP")
	def op22(op,i):
		incrsp(1)
		loadconst(getch)
		emitoparg("CALL_FUNCTION",0)
	def op23(op,i):
		incrsp(1)
		loadconst(int)
		loadconst(input)
		emitoparg("CALL_FUNCTION",0)
		emitoparg("CALL_FUNCTION",1)
	def op24(op,i):
		spguard(2,-1)
		loadconst(rmem)
		emit("ROT_THREE")
		emitoparg("CALL_FUNCTION",2)
	def op25(op,i):
		spguard(3,-3)
		storefast(1)
		loadconst(wmem)
		emit("ROT_THREE")
		loadfast(1)
		emitoparg("CALL_FUNCTION",3)
		emit("DUP_TOP")
		emitoparg("POP_JUMP_IF_FALSE", len(r)+4)
		emit("RETURN_VALUE")
		emit("POP_TOP")
	def op26(op,i):
		loadconst(rng)
		emitoparg("CALL_FUNCTION",0)
		offsets = []
		for a in range(3):
			emit("DUP_TOP")
			loadconst(a)
			emitoparg("COMPARE_OP",2)
			offsets.append(len(r))
			emitoparg("POP_JUMP_IF_TRUE",0)
		offsets.append(len(r))
		emitoparg("JUMP_ABSOLUTE",0)
		patch(offsets,(compile(i&~3|a,1) for a in range(4)))
		return -1
	def opIF(op,i):
		spguard(1,-1)
		loadconst(0)
		emitoparg("COMPARE_OP",2)
		offsets = [len(r)]
		emitoparg("POP_JUMP_IF_TRUE",0)
		offsets.append(len(r))
		emitoparg("JUMP_ABSOLUTE",0)
		patch(offsets,(compile(i&~3|(3-a*2 if op==27 else a*2)) for a in range(2)))
		return -1
	def op29(op,i):
		i=mv(i)
		n=0
		while ps[i>>2]!=34:
			loadconst(ps[i>>2])
			i=mv(i)
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
	def compile(i,pop=0):
		ret = len(r)
		if pop is None:
			loadconst(0)
			storefast(0)
		else:
			for op in range(pop):emit("POP_TOP")
		i=mv(i)
		while True:
			if pg[i] != -1:
				emitoparg("JUMP_ABSOLUTE", pg[i])
				return ret
			pg[i]=len(r)
			op = getop(ps[i>>2])
			setpro(i)
			ni=opfs[op](op,i)
			if ni is not None:
				if ni == -1:return ret
				else:i=ni
			i=mv(i)
	compile(10112,None)
	def prog():
		do=True
		while do:
			f=FunctionType(CodeType(0,0,2,65536,0,bytes(r),tuple(consts),(),("s","t"),"","",0,b""),{})
			if debug:
				from dis import dis
				dis(f)
			do=f()
	return prog
if __name__ == "__main__":
	from sys import argv
	pre0 = -int(argv[2]) if len(argv) > 2 and argv[2].isdigit() else 0
	debug = "d" in argv
	main(open(argv[1]).read(),pre0)()
