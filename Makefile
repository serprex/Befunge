all: funge fungesafe marsh
funge: funge.c
	gcc -std=gnu99 funge.c -O3 -march=native -fmerge-all-constants -fomit-frame-pointer -fno-gcse -S
	./fixit.py funge.s
	as funge.s -o funge.o
	gcc funge.o -o funge
	strip funge
fungesafe: fungesafe.c
	gcc -std=gnu99 fungesafe.c -O3 -march=native -fmerge-all-constants -fomit-frame-pointer -fno-gcse -S
	./fixit.py fungesafe.s
	as fungesafe.s -o fungesafe.o
	gcc fungesafe.o -o fungesafe
	strip fungesafe
marsh: marsh.c
	gcc -std=gnu99 marsh.c -O3 -march=native -fmerge-all-constants -fomit-frame-pointer -fno-gcse -S
	./fixit.py marsh.s
	as marsh.s -o marsh.o
	gcc marsh.o -o marsh
	strip marsh
