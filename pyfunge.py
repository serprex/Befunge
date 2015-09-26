#!/bin/python
from sys import stdout
def getch():
	try:import termios
	except ImportError:
		from msvcrt import getch
		return getch
	from sys import stdin
	from tty import setraw
	def getch():
		fd=stdin.fileno()
		retset=termios.tcgetattr(fd)
		try:
			setraw(fd)
			return stdin.read(1)
		finally:termios.tcsetattr(fd, termios.TCSADRAIN, retset)
	return getch
getch = getch()

def main(pstring):
	from opcode import opmap
	from types import CodeType,FunctionType
	from random import randint
	loc = bytes((16,29,31,17,14,23,36,36,36,12,10,21,11,20,13,0,1,2,3,4,5,6,7,8,9,18,36,34,36,32,26,30,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,36,19,36,33,28,15,36,36,36,36,36,36,24,36,36,36,36,36,36,36,36,25,36,36,36,36,36,35,36,36,36,36,36,27,36,22));
	ps = [0]*2560
	pstring = pstring.split("\n")
	for y,line in enumerate(pstring):
		if y>25:break
		for x,c in enumerate(line):
			if x>80:break
			ps[x<<5|y]=ord(c)
	pg = [-1]*10240
	def rmem(x,y):return ps[x<<5|y] if 0<=x<=80 and 0<=y<=25 else 0
	def wmem(x,y,v):ps[x<<5|y] = v
	def rng():return randint(0,3)
	pro = bytearray((0,))*640
	r = bytearray()
	def getop(i):return loc[i-33] if 33<=i<=126 else 36
	def emit(op):r.append(opmap[op])
	consts = []
	names = []
	def emitidx(a,c):
		if c in a:
			emitarg(a.index(c))
		else:
			emitarg(len(a))
			a.append(c)
	def loadconst(c):
		r.append(100)
		emitidx(consts, c)
	args = "ps","int","chr","print","putch","input","getch","wmem","rmem","rng"
	def loadarg(c):
		r.append(124)
		emitarg(args.index(c))
	def storefast(x):
		r.append(125)
		emitarg(len(args)+x)
	def loadfast(x):
		r.append(124)
		emitarg(len(args)+x)
	def emitoparg(op,arg):
		emit(op)
		emitarg(arg)
	def emitarg(arg):
		r.extend((arg&255,arg>>8))
	def mv(i):
		i3=i&3
		return (
			(i-10112 if i>=10112 else i+128) if i3==0 else
			(i-4 if i&124 else i+96) if i3==1 else
			(i+10112 if i<128 else i-128) if i3==2 else
			(i+4 if (i+4&124)<100 else i-96))
	def setpro(i):pro[i>>4]|=1<<(i>>1&6)
	def getpro(i):return pro[i>>4]&(1<<(i>>1&6))
	def opC(op,i):loadconst(op)
	def op10(op,i):emit("BINARY_ADD")
	def op11(op,i):emit("BINARY_SUB")
	def op12(op,i):emit("BINARY_MULTIPLY")
	def op13(op,i):emit("BINARY_FLOOR_DIVIDE")
	def op14(op,i):emit("BINARY_MODULO")
	def op15(op,i):emitoparg("COMPARE_OP",4)
	def op16(op,i):emit("UNARY_NOT")
	def op17(op,i):emit("POP_TOP")
	def op18(op,i):emit("DUP_TOP")
	def op19(op,i):emit("ROT_TWO")
	def op20(op,i):
		loadarg("print")
		emit("ROT_TWO")
		emitoparg("CALL_FUNCTION",1)
		emit("POP_TOP")
	def op21(op,i):
		loadarg("chr")
		emit("ROT_TWO")
		emitoparg("CALL_FUNCTION",1)
		loadarg("putch")
		emit("ROT_TWO")
		emitoparg("CALL_FUNCTION",1)
		emit("POP_TOP")
	def op22(op,i):
		loadarg("getch")
		emitoparg("CALL_FUNCTION",0)
	def op23(op,i):
		loadarg("int")
		loadarg("input")
		emitoparg("CALL_FUNCTION",0)
		emitoparg("CALL_FUNCTION",1)
	def op24(op,i):
		loadarg("rmem")
		emit("ROT_THREE")
		emitoparg("CALL_FUNCTION",2)
	def op25(op,i):
		storefast(0)
		loadarg("wmem")
		emit("ROT_THREE")
		loadfast(0)
		emitoparg("CALL_FUNCTION",3)
		emit("POP_TOP")
	def op26(op,i):
		p=[compile(i&~3|a,1) for a in range(4)]
		loadarg("rng")
		emitoparg("CALL_FUNCTION",0)
		for a in range(3):
			emit("DUP_TOP")
			loadconst(a)
			emitoparg("COMPARE_OP",2)
			emitoparg("POP_JUMP_IF_TRUE",p[a])
		emitoparg("JUMP_ABSOLUTE",p[3])
	def opIF(op,i):
		p=[compile(i&~3|(3-a*2 if op==27 else a*2)) for a in range(2)]
		loadconst(0)
		emitoparg("COMPARE_OP",2)
		emitoparg("POP_JUMP_IF_TRUE",p[0])
		emitoparg("JUMP_ABSOLUTE",p[1])
	def op29(op,i):
		i=mv(i)
		while ps[i>>2]!=34:
			loadconst(ps[i>>2])
			i=mv(i)
		return i
	def op30(op,i):
		emit("RETURN_VALUE")
		return -1
	def op31(op,i):return mv(i)
	def opDIR(op,i):return i&~3|op&3
	def op36(op,i):pass
	opfs = (opC,opC,opC,opC,opC,opC,opC,opC,opC,opC,op10,op11,op12,
		op13,op14,op15,op16,op17,op18,op19,op20,op21,op22,op23,op24,
		op25,op26,opIF,opIF,op29,op30,op31,opDIR,opDIR,opDIR,opDIR,op36)
	def compile(i,pop=0):
		for op in range(pop):emit("POP_TOP")
		while True:
			op = getop(ps[i>>2])
			#print(op, i)
			opf = opfs[op]
			if pg[i] != -1:return emitoparg("JUMP_ABSOLUTE", pg[i])
			setpro(i)
			pg[i]=len(r)
			ni=opf(op,i)
			if ni is not None:
				if ni == -1:return
				else:i=ni
			i=mv(i)
	compile(0)
	f=FunctionType(CodeType(len(args),0,len(args)+1,65536,0,bytes(r),tuple(consts),(),args,"","",0,b""),{})
	from dis import dis
	dis(f)
	return lambda:f(ps, int, chr, print, stdout.write, input, getch, wmem, rmem, rng)
f=main(r"""0"Hello",,,,,@""")
f()
