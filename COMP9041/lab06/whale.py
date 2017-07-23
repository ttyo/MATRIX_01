#!/usr/bin/python2.7

import sys
import re

key = sys.argv[1]
pod = 0
counter = 0
inputlines = []

for line in sys.stdin:
	line = re.sub(r" +", " ", line)
	line = re.sub(r"\n", "", line)
	sp = line.split(" ", 1)
	number = int(sp[0])
	name = sp[1]

	if (name == key):
		pod += 1
		counter += number

print (key + " observations: " + str(pod) + " pods, " + str(counter) + " individuals")
