#!/bin/bash

echo "hello world"
if test -r /dev/null
then
    echo a
fi
if test -r nonexistantfile
then
    echo b
fi

if test -d /dev/null
then
    echo /dev/null
fi
if test -d /dev
then
    echo /dev
fi

# l [file|directories...] - list files
# written by andrewt@cse.unsw.edu.au as a COMP2041 example
ls -las "$@"
# a=a+b

# print a contiguous integer sequence
start=$1
finish=$2

number=$start
while test $number -le $finish
do
    echo $number
    number=`expr $number + 1`  # increment number
done

echo "new line"
echo -n "new line"
