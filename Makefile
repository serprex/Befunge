CF = -O3 -march=native -fmerge-all-constants -fno-gcse -fomit-frame-pointer
CC = gcc -std=gnu99
all: funge marsh
funge: marsh.c
	${CC} -DFUNGE marsh.c -o funge.s -S ${CF}
	./fixit.py funge.s
	as funge.s -o funge.o
	gcc funge.o -o funge
	strip funge
marsh: marsh.c
	${CC} marsh.c -o marsh.s -S ${CF}
	./fixit.py marsh.s
	as marsh.s -o marsh.o
	gcc marsh.o -o marsh
	strip marsh
clean:
	rm *.o *.s
