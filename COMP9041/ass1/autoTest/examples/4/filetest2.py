#!/usr/bin/python2.7 -u
import os.path
if os.path.isdir('/dev/null'):
    print '/dev/null'
if os.path.isdir('/dev'):
    print '/dev'
