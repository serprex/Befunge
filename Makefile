all: funge marsh
funge: funge.c
	gcc -std=gnu99 funge.c -O3 -march=native -fmerge-all-constants -fomit-frame-pointer -fno-gcse -S
	python fixit.py
	as funge.s -o funge.o
	gcc funge.o -o funge
	strip funge
marsh: marsh.c
	gcc -std=gnu99 marsh.c -O3 -march=native -fmerge-all-constants -fomit-frame-pointer -fno-gcse -S
	python fixit.py
	as marsh.s -o marsh.o
	gcc marsh.o -o marsh
	strip marsh
