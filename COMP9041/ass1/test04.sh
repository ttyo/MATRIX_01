#!/bin/bash
# failed part

echo \"may the force be with you\'
echo a echo b echo c
echo a;echo b;echo c

if test -r /dev/null && test a = a || [ -r nonexistantfile ]
then print a
else print b fi

a=$(expr 1 + 2)

a=1
while test $a -lt 5
do echo $a;a=`expr $a + 1`;
done
