#!/usr/bin/python
import sys
import re
import subprocess

order = 0;
#index = 1;
result = []
table = {}
#if (sys.argv[0] == "-f"):
#	order = 1;
#	index = 2;

for url in sys.argv[1:]:
	if (url == "-f"):
		order = 1
	else:
		F = subprocess.Popen(["wget","-q","-O-",url], stdout=subprocess.PIPE)
		for line in iter(F.stdout.readline, ""):
			result += re.findall(r'<[^!][^>]*>', line)

		for temp in result:
			temp = re.sub(r'\s[^>]*>', '>', temp)
			temp = temp.replace("<", ">")
			temp = temp.replace("/", ">")
			temp = temp.replace(">", "")
			tag = temp.lower()
			table.setdefault(tag, 0)
			table[tag] += 1

	
		if (order == 0):
			for key in sorted(table):
				print ("{} {}".format(key, table[key]/2))
		else:
			for key in sorted(table, key=table.get):
				print ("{} {}".format(key, table[key]/2))

