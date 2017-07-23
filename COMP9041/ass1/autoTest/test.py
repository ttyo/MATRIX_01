#!/usr/bin/python2.7 -u
import os,shutil	
shutil.move('1', '111')	
if os.access('111' , os.R_OK):	
	
	print 'exit 111'	
else :	
	print 'not exit 111'	
