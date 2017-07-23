#!/usr/bin/python2.7 -u
import subprocess
import sys
# l [file|directories...] - list files
# written by andrewt@cse.unsw.edu.au as a COMP2041 example

subprocess.call(['ls', '-las'] + sys.argv[1:])
