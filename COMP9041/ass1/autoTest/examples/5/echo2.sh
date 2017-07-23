#!/bin/sh

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
