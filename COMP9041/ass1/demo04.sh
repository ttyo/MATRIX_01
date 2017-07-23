#!/bin/bash

aa=1
bb=2
cc=3
dd=4
vv=5
echo "$bb"
echo $bb
echo "aa bb $cc $dd ee"
echo aa bb $cc $dd ee
echo "$cc $vv aa bb"
echo $cc $vv aa bb

echo "$cc$vv"
echo $cc$vv

echo "aa$vv"
echo aa$vv

echo "xx vv $cc$vv"
echo xx vv $cc$vv

echo "xx vv $cc$vv dd ee"
echo xx vv $cc$vv dd ee

echo $#
echo $@
echo $*

if [ -d /dev/null ] # COMMENT
then # COMMENT
    echo /dev/null
fi # COMMENT
if [ -d /dev ]
then # COMMENT
    echo /dev
fi

rm /test/ex.txt
if test -r /test/ex.txt
then 
    echo yes
    mv /test/ex.txt /test/new/
else
    echo no
fi

start=$1
finish=$2

number=$start
while [ $number -le $finish ]
do
    echo $number
    number=$(($number + 1)) # COMMENT
done

start=13
if test $# -gt 0
then
    start=$1
fi
i=0
number=$start
file=./tmp.numbers # COMMENT
rm -f $file
while true # COMMENT
do
    if test -r $file # COMMENT
    then # COMMENT
        if fgrep -x -q $number $file # COMMENT
        then # COMMENT
            for i in {1..5}
            do
                echo "nested content"
            done
            echo Terminating because series is repeating
            exit 0
        fi
    fi
    echo $number >>$file
    echo $i $number
    k=`expr $number % 2`
    if test $k -eq 1 # COMMENT
    then
        number=`expr 7 '*' $number + 3`
    else
        number=`expr $number / 2`
    fi
     i=`expr $i + 1`
    if test $number -gt 100000000 -o  $number < -100000000 
    then # COMMENT
        echo Terminating because series has become too large
        exit 0
    fi
done
rm -f $file

case $FRUIT in
    "apple")
        echo "Apple pie is quite tasty." 
        number=$number + 1
    ;;
    "banana") 
        echo "I like banana nut bread."
        number=`expr $number + 1`
    ;;
    "kiwi")
        echo "New Zealand is famous for kiwi." 
         chmod -rw-rw-r-- $file # COMMENT     
         chmod -rwxrwxrwx '~/test' # COMMENT
    ;;
esac


test=2
case $test in
   0) echo "test = 1";;
   1) echo "test = 2";;
   2) echo "test = 3";;
   *) echo "failed";;
esac



