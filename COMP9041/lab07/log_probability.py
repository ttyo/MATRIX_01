#!/usr/bin/python

import sys
import glob
import re
import math

result = []
key = (sys.argv[1]).lower()
for poet in glob.glob("poets/*.txt"):
	count = []
	subresult = []
	F = open(poet, 'r')
	for line in F:
		line = line.lower()
		count += re.split(r"[^A-Za-z]", line)

	filename = poet.replace(".txt", "")
	filename = filename.replace("_", " ")
	filename = filename.replace("poets/", "")

	count = filter(None, count)
	length = len(count)
	keynumber = count.count(key)
	subresult.append(filename)
	subresult.append(length)
	subresult.append(keynumber)
	result.append(subresult)

result.sort()
for sub in result:
	print ("log(({:d}+1)/{:6d}) = {:8.4f} {}".format(sub[2], sub[1], math.log((float(sub[2])+1)/float(sub[1])), sub[0]))
