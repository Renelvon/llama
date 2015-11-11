FLAGS= -Wall -std=gnu11 -march=native -Os
LINKFLAGS= -lm
CC=clang-3.5

.PHONY: clean test

libtest: libllama.o libtest.o
	$(CC) $(FLAGS) $(LINKFLAGS) $^ -o $@

libtest.o: libtest.c libllama.h
	$(CC) $(FLAGS) -c $< -o $@

libllama.o: libllama.c
	$(CC) $(FLAGS) -c $< -o $@

clean:
	$(RM) *.o libtest

test: libtest
	./libtest
