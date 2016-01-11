#!/usr/bin/python

import sys
import re

count = []
for line in sys.stdin:
	count += re.split(r"[^A-Za-z]", line)

count = filter(None, count)
len = len(count)
print (str(len) + " words")
