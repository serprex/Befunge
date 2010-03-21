all: goto marsh
goto: goto.c
	gcc -std=gnu99 goto.c -O3 -march=native -fmerge-all-constants -fomit-frame-pointer -fno-gcse -S
	python fixit.py
	as goto.s -o goto.o
	gcc goto.o -o goto
	strip goto
marsh: marsh.c
	gcc -std=gnu99 marsh.c -O3 -march=native -fmerge-all-constants -fomit-frame-pointer -fno-gcse -S
	python fixit.py
	as marsh.s -o marsh.o
	gcc marsh.o -o marsh
	strip marsh
