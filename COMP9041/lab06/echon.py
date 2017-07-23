#!/usr/bin/python2.7

import sys

if (len(sys.argv) != 3):
	print ("Usage: ./echon.py <number of lines> <string>")
else:
	for num in range(0, int(sys.argv[1])):
		print (sys.argv[2])
