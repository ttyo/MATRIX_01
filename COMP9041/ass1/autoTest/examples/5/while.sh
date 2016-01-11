#!/bin/sh
a=1
while test $a -lt 5
do echo $a;a=`expr $a + 1`;
done