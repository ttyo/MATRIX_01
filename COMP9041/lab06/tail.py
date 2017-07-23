#!/usr/bin/python2.7

import sys

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

for filename in sys.argv[1:]:
	file = open(filename)
	lines = file_len(filename)
	index = 0
	if (lines > 10):
		index = lines - 10

	for i, line in enumerate(file):
		if (i == index):
			print (line.rstrip("\n"))
			index += 1
