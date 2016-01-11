#!/usr/bin/python

import sys
import re

count = []
key = (sys.argv[1]).lower()
for line in sys.stdin:
	pattern = re.compile(r"\b%s\b" %key, re.IGNORECASE)
	count += re.findall(pattern, line)
print (key + " occurred " + str(len(count)) + " times")
