#!/usr/bin/python2.7 -u
import sys

for n in 'one', 'two', 'three':
    line = sys.stdin.readline().rstrip()
    print 'Line', n, line
