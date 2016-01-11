#!/bin/sh
start=13
if test $# -gt 0
then
    start=$1
fi
i=0
number=$start
file=./tmp.numbers
rm -f $file
while true # a while loop
do
    if test -r $file # a nested if
    then
        if fgrep -x -q $number $file # another nested if
        then
            echo Terminating because series is repeating
            exit 0
        fi
    fi
    echo $number >>$file
    echo $i $number
    k=`expr $number % 2`
    if test $k -eq 1 # another nested if
    then
        number=`expr 7 '*' $number + 3`
    else
        number=`expr $number / 2`
    fi
     i=`expr $i + 1`
    if test $number -gt 100000000 -o  $number -lt -100000000 
    then
        echo Terminating because series has become too large
        exit 0
    fi
done
rm -f $file
