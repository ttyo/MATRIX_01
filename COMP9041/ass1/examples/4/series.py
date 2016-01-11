#!/usr/bin/python2.7 -u
import os
import subprocess
import sys
start = 13
if len(sys.argv[1:]) > 0:
    start = sys.argv[1]
i = 0
number = start
file = './tmp.numbers'
subprocess.call(['rm', '-f', str(file)])
while not subprocess.call(['true']):
    if os.access(file, os.R_OK):
        if not subprocess.call(['fgrep', '-x', '-q', str(number), str(file)]):
            print 'Terminating', 'because', 'series', 'is', 'repeating'
            sys.exit(0)
    with open(file, 'a') as f: print >>f,  number
    print i, number
    k = int(number) % 2
    if k == 1:
        number = 7 * int(number) + 3
    else:
        number = int(number) / 2
    i = i + 1
    if int(number) > 100000000 or int(number) < -100000000:
        print 'Terminating', 'because', 'series', 'has', 'become', 'too', 'large'
        sys.exit(0)
subprocess.call(['rm', '-f', str(file)])
