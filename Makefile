ifneq ($(FLT),)
LF=-DW$(FLT) -lm
endif
all:
	gcc -std=gnu99 marsh.c -o marsh -O3 -s -march=native -fwhole-program ${LF} -DWBIT=64
	gcc -std=gnu99 bejit.c -o bejit -O3 -s -march=native -fwhole-program ${LF}