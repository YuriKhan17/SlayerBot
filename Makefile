# Makefile for compiling the fake Pyahmed trap
all:
	gcc -shared -fPIC -o Pyahmed.so Fake.c
