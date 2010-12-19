ifneq ($(FLT),)
LF=-DW$(FLT) -lm
endif
all:
	gcc -std=gnu99 marsh.c -o marsh -O3 -s -march=native -fwhole-program ${LF} -DWBIT=32 -DSPACE=32