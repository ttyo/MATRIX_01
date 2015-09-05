#!/usr/bin/python2.7

import sys
import re

whale = []
pod = []
counter = []
result_list = []

for line in sys.stdin:
	line = re.sub(r" +", " ", line)
	line = re.sub(r"\n", "", line)
	line = re.sub(r" +$", "", line)
	line = line.lower()
	sp = line.split(" ", 1)

	number = int(sp[0])
	key = sp[1]
	if (re.match(r".+s$", key)):
		key = key[:-1]

	notnew = 0
	if (len(whale) == 0):
                whale.append(key)
		pod.append(1)
		counter.append(number)
		notnew = 1;
	else:
		for i in range(0, len(whale)):
			if (whale[i] == key):
				pod[i] += 1
				counter[i] += number
				notnew = 1
				break

	if (notnew == 0):
                whale.append(key)
		pod.append(1)
		counter.append(number)
	
for i in range(0, len(whale)):
	result = whale[i] + " observations: " + str(pod[i]) +" pods, " + str(counter[i]) + " individuals"
	result_list.append(result)

result_list.sort()
for i in range(0, len(whale)):
	print result_list[i]
