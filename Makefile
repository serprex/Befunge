CF = -O3 -march=native -fmerge-all-constants -fomit-frame-pointer -fno-gcse
CC = gcc -std=gnu99
all: funge fungesafe marsh marshsafe
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
fungesafe: marshsafe.c
	${CC} -DFUNGE marshsafe.c -o fungesafe.s -S ${CF}
	./fixit.py fungesafe.s
	as fungesafe.s -o fungesafe.o
	gcc fungesafe.o -o fungesafe
	strip fungesafe
marshsafe: marshsafe.c
	${CC} marshsafe.c -o marshsafe.s -S ${CF}
	./fixit.py marshsafe.s
	as marshsafe.s -o marshsafe.o
	gcc marshsafe.o -o marshsafe
	strip marshsafe
clean:
	rm *.o *.s
