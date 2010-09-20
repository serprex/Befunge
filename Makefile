all:
	gcc -std=gnu99 marsh.c -o marsh -O3 -s -march=native -fwhole-program