CF = -O3 -march=native -fwhole-program -s
CC = gcc -std=gnu99
all: funge marsh
funge: marsh.c
	${CC} -DFUNGE marsh.c -o funge ${CF}
marsh: marsh.c
	${CC} marsh.c -o marsh ${CF}