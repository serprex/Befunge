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
	ps = [0]*2560
	for y,line in enumerate(pro):
		if y>=25:break
		for x,c in enumerate(line):
			if x>=80:break
			ps[x<<5|y]=c
	pg={}
	consts=[]
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
					consts[:]=()
					pro.clear()
					pg.clear()
					return compile(i,s)
			return False
		return f
	def emit(op,arg=None):
		r.append(opmap[op])
		if arg is not None:return emitarg(arg)
	def mkemit(op):
		op = opmap[op]
		return (lambda:r.append(op)) if op<HAVE_ARGUMENT else (lambda a:r.extend((op,a&255,a>>8)))
	swap = mkemit("ROT_TWO")
	rot3 = mkemit("ROT_THREE")
	pop = mkemit("POP_TOP")
	dup = mkemit("DUP_TOP")
	call = mkemit("CALL_FUNCTION")
	jump = mkemit("JUMP_ABSOLUTE")
	def popcall(arg):
		call(arg)
		return pop()
	def patch(loc,off):
		r[loc+1]=off&255
		r[loc+2]=off>>8
	def load(c):
		nonlocal consts
		r.append(100)
		isint = type(c) == int
		for (i, a) in enumerate(consts):
			if (c==a if isint else c is a):return emitarg(i)
		emitarg(len(consts))
		consts += c,
	putint = lambda x:print(+x,end=' ')
	def emitarg(arg):return r.extend((arg&255,arg>>8))
	def incr(n):
		if n:
			load(n)
			return emit("BINARY_ADD")
	def prbug(x, oneline=False):
		if not debug:return
		load(print)
		load(x)
		if oneline:
			load("end")
			load(" ")
			load("flush")
			load(True)
		return popcall(513 if oneline else 1)
	def prtop():
		dup()
		load(print)
		swap()
		load("\tDepth")
		swap()
		load("flush")
		load(True)
		return popcall(258)
	def spguard(f,n=0):
		if debug:prtop()
		if f==1:
			emit("JUMP_IF_TRUE_OR_POP",len(r)+8)
			load(0)
			dup()
			swap()
			return incr(n)
		else:
			i=len(r)
			jump(0)
			load(1)
			emit("BINARY_ADD")
			load(0)
			swap()
			patch(i,len(r))
			dup()
			load(f-1)
			emit("COMPARE_OP",4)
			emit("POP_JUMP_IF_FALSE",i+3)
			return incr(n)
	def mv(i):
		i3=i&3
		return (
			(i-10112 if i>=10112 else i+128) if i3==0 else
			(i-4 if i&124 else i+96) if i3==1 else
			(i+10112 if i<128 else i-128) if i3==2 else
			(i+4 if (i+4&124)<100 else i-96))
	def opC(op,i):
		incr(1)
		load(op)
		return swap()
	def binOp(name):
		def g(op,i):
			spguard(2,-1)
			rot3()
			emit(name)
			return swap()
		return g
	op10=binOp("BINARY_ADD")
	op11=binOp("BINARY_SUBTRACT")
	op12=binOp("BINARY_MULTIPLY")
	op13=binOp("BINARY_FLOOR_DIVIDE")
	op14=binOp("BINARY_MODULO")
	def op15(op,i):
		spguard(2,-1)
		rot3()
		emit("COMPARE_OP",4)
		return swap()
	def op16(op,i):
		spguard(1)
		swap()
		emit("UNARY_NOT")
		return swap()
	def op17(op,i):
		dup()
		i=len(r)
		emit("POP_JUMP_IF_FALSE",0)
		incr(-1)
		swap()
		pop()
		return patch(i,len(r))
	def op18(op,i):
		spguard(1,1)
		swap()
		dup()
		rot3()
		return rot3()
	def op19(op,i):
		spguard(2)
		rot3()
		swap()
		rot3()
		return rot3()
	def op20(op,i):
		spguard(1,-1)
		swap()
		load(putint)
		swap()
		return popcall(1)
	def op21(op,i):
		spguard(1,-1)
		swap()
		load("%c")
		swap()
		emit("BINARY_MODULO")
		load(stdout.write)
		swap()
		return popcall(1)
	def op22(op,i):
		incr(1)
		load(getch)
		call(0)
		return swap()
	def op23(op,i):
		incr(1)
		load(int)
		load(input)
		call(0)
		call(1)
		return swap()
	def op24(op,i):
		spguard(2,-1)
		rot3()
		swap()
		load(5)
		emit("BINARY_LSHIFT")
		emit("BINARY_OR")
		dup()
		load(0)
		emit("COMPARE_OP",0)
		j=len(r)
		emit("POP_JUMP_IF_TRUE",0)
		dup()
		load(2560)
		emit("COMPARE_OP",5)
		j2=len(r)
		emit("POP_JUMP_IF_TRUE",0)
		load(ps)
		swap()
		emit("BINARY_SUBSCR")
		j3=len(r)
		jump(0)
		patch(j,len(r))
		patch(j2,len(r))
		emit("UNARY_NOT")
		patch(j3,len(r))
		return swap()
	def op25(op,i):
		spguard(3,-3)
		emit("BUILD_TUPLE",4)
		dup()
		load(3)
		emit("BINARY_SUBSCR")
		swap()
		load(wmem(i))
		swap()
		call(1)
		j=len(r)
		emit("POP_JUMP_IF_FALSE",0)
		emit("BUILD_LIST",0)
		swap()
		dup()
		j2=len(r)
		emit("POP_JUMP_IF_FALSE",0)
		rot3()
		swap()
		emit("BUILD_TUPLE",1)
		emit("INPLACE_ADD")
		swap()
		load(1)
		emit("BINARY_SUBTRACT")
		jump(j2-1)
		pop()
		emit("RETURN_VALUE")
		i=len(r)
		patch(j,i)
		return patch(j2,i-2)
	def op26(op,i):
		load(getrandbits)
		load(2)
		call(1)
		dup()
		offsets = [len(r)]
		emit("POP_JUMP_IF_FALSE",0)
		for a in 1,2:
			dup()
			load(a)
			emit("COMPARE_OP",2)
			offsets += (len(r),)
			emit("POP_JUMP_IF_TRUE",0)
		for a in 0,1,2,3:
			if a:patch(offsets[a-1],len(r))
			compile(i&~3|a,True)
		return -1
	def opIF(op,i):
		spguard(1,-1)
		swap()
		j = len(r)
		emit("POP_JUMP_IF_TRUE",0)
		for a in 0,1:
			if a==1:patch(j,len(r))
			compile(i&~3|(3-a*2 if op==27 else a*2))
		return -1
	def op29(op,i):
		n=0
		while True:
			i=mv(i)
			i2=i>>2
			pro.add(i2)
			op=ps[i2]
			if op==34:
				incr(n)
				return i
			load(op)
			swap()
			n+=1
	def op30(op,i):
		load(True)
		emit("RETURN_VALUE")
		return -1
	def op31(op,i):return mv(i)
	def opDIR(op,i):return i&~3|op&3
	def op36(op,i):pass
	opfs=(opC,)*10+(op10,op11,op12,op13,op14,op15,op16,op17,op18,op19,op20,op21,op22,
		op23,op24,op25,op26,opIF,opIF,op29,op30,op31,opDIR,opDIR,opDIR,opDIR,op36)
	def compile(i,popflag=False):
		if popflag is True:pop()
		elif popflag is not False:load(popflag)
		while True:
			i=mv(i)
			if i in pg:
				if debug:prbug("JUMP%s"%pg[i])
				jump(pg[i])
				return True
			pg[i]=len(r)
			i2 = i>>2
			pro.add(i2)
			i2 = ps[i2]
			op = b'\x10\x1d\x1f\x11\x0e\x17$$$\x0c\n\x15\x0b\x14\r\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\x12$"$ \x1a\x1e$$$$$$$$$$$$$$$$$$$$$$$$$$$\x13$!\x1c\x0f$$$$$$\x18$$$$$$$$\x19$$$$$#$$$$$\x1b$\x16'[i2-33] if 33<=i2<=126 else 36
			if debug and op < 31:prbug("op %c %d"%(i2,op))
			i2=opfs[op](op,i)
			if i2 is not None:
				if i2 == -1:return True
				else:i=i2
	compile(10112,0)
	def stackfix(a):
		nonlocal consts
		for i,a in zip(range(len(a)*3-2,0,-3),a):
			if a in consts:a=consts.index(a)
			else:
				consts += a,
				a=len(consts)-1
			r[i]=a&255
			r[i+1]=a>>8
	while True:
		f=FunctionType(CodeType(0,0,0,65536,0,bytes(r),tuple(consts),(),(),"","",0,b""),{})
		if debug>1 or "dis" in argv:
			from dis import dis
			dis(f)
		do=f()
		if do is True:return
		if debug:print("Return", do)
		stackfix(do)
if __name__ == "__main__":
	from sys import argv
	debug = argv.count("d")
	main(open(argv[1],"rb"),argv)
