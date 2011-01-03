ifneq ($(FLT),)
LF=-DW$(FLT) -lm
endif
all:marsh bejit
marsh:marsh.c marsh.h
	gcc -std=gnu99 marsh.c -o marsh -O3 -s -march=native -fwhole-program ${LF} -DWBIT=32
bejit:bejit.c
	gcc -std=gnu99 bejit.c -o bejit -O0 -g -march=native -fwhole-program