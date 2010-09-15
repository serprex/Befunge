CF = -O3 -march=native -fmerge-all-constants -fno-gcse -fwhole-program
CC = gcc -std=gnu99
all: funge marsh
funge: marsh.c
	${CC} -DFUNGE marsh.c -o funge ${CF}
marsh: marsh.c
	${CC} marsh.c -o marsh ${CF}