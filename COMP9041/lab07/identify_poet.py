#!/usr/bin/python

import sys
import glob
import re
import math

debug = 0
input = []
for arg in sys.argv[1:]:
	if (arg == "-d"):
		debug = 1
	elif (arg == "poem?.txt"):
		for poem in glob.glob("*.txt"):
			if (r.match(r"poem[0-9]+.txt", poem)):
				input.append(poem)
		input.sort()
	else:
		input.append(arg)

poetlist = []
poetkeylist = []
for poet in glob.glob("poets/*.txt"):
	poetlist.append(poet)
	poet = poet.replace(".txt", "")
	poet = poet.replace("_", " ")
	poet = poet.replace("poets/", "")
	poetkeylist.append(poet)

for poem in input:
	poemwordslist = []
	PM = open(poem, 'r')
	for line in PM:
		line = line.lower()
		poemwordslist += re.split(r"[^A-Za-z]", line)
	poemwordslist = filter(None, poemwordslist)

	poetwordstotal = {}
	poetwordscounter = {}
	for poet in poetlist:
		poetwordslist = []
		PT = open(poet, 'r')
		poet = poet.replace(".txt", "")
		poet = poet.replace("_", " ")
		poet = poet.replace("poets/", "")

		for line in PT:
			line = line.lower()
			poetwordslist += re.split(r"[^A-Za-z]", line)
			#for word in line:
			#	if word:
			#		poetwordscounter.setdefault((poet, word), 0)
			#		poetwordscounter[poet, word] = poetwordscounter[poet, word] + 1

		poetwordslist = filter(None, poetwordslist)
		for word in poetwordslist:
			poetwordscounter.setdefault((poet, word), 0)
			poetwordscounter[poet, word] = poetwordscounter[poet, word] + 1
		poetwordstotal[poet] = len(poetwordslist)

	resultcounter = {}
	result = {}
	for wordpm in poemwordslist:
		for poet in poetkeylist:
			resultcounter[wordpm] = poetwordscounter.setdefault((poet, wordpm), 0)
			result.setdefault(poet, 0)
			result[poet] += math.log((float(resultcounter[wordpm]) + 1) / float(poetwordstotal[poet]))
	
	sortedkeylist = sorted(result, key=result.get, reverse=True)
	most = sortedkeylist[0]
	if debug:
		for key in sortedkeylist:
			print("{}: log_probability of {:5.1f} for {}".format(poem, result[key], key))
	print ("{} most resembles the work of {} (log-probability={:5.1f})".format(poem, most, result[most]))


