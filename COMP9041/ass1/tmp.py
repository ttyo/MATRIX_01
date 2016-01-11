#!/usr/bin/python2.7 -u
if os.access('/dev/null', os.R_OK):
    print 'a'
if os.access('nonexistantfile', os.R_OK):
    print 'b'
