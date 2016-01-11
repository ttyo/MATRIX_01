#!/bin/bash
cd /tmp
pwd

for word in Houston 1202 alarm
do
    echo $word
    exit 0
done

for c_file in *.c
do
    echo gcc -c $c_file
done

for n in one two three
do
    read line
    echo Line $n $line
done
