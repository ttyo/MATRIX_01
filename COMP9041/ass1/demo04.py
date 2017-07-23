#!/usr/bin/python2.7 -u
import subprocess
import os
import glob
import os.path
import sys
# nested if in for loop
# nested while in nested if in for
# nested if in nested while in nested if in for
# comments everywhere
# double/single quotes to variable
# mv command
# chmod command
# echo -n
# many whitespaces after lines
# the number of tab before lines is not always 4 * n
# case ... esac

FRUIT = "kiwi"
number = 1
dir_demo = 'usr/bin/sou/temp'
dir = "usr/bin/sou/temp" # COMMENT
for files in sorted(glob.glob("~/tmp/*.txt")): # COMMENT
    if os.path.exists(str(files)): # COMMENT
        subprocess.call(['mv', str(files), str(dir)], shell = True)
        start = sys.argv[1]
        finish = sys.argv[2]

        number = start
        while int(number) <= int(finish):
            if int(number) > 100000000 and int(number) < -100000000:
                print 'Terminating', 'because', 'series', 'has', 'become', 'too', 'large'
                sys.exit(0)
            print number
            number = int(number) + 1 # COMMENT
            number = number
    # COMMENT
    else:
        file = '~/tmp/*.txt'
        os.chmod(str(file), 0664) # 664
        os.chmod('~/test', 0777) # 777
        print "begin print: ",
        print "no files to move"

def APPLE ():
    print "Apple pie is quite tasty."
    number = number + 1

def BANANA ():
    print "I like banana nut bread."
    number = int(number) + 1

def KIWI ():
    print "New Zealand is famous for kiwi."
    os.chmod(str(file), 0664) # 664
    os.chmod('~/test', 0777) # 777

case_esac = {
    "apple":APPLE,
    "banana":BANANA,
    "kiwi":KIWI
}

case_esac[FRUIT]()



