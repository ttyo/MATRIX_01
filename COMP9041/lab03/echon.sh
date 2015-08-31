#!/bin/bash

# $# - number of variables, maximum is 4
# $@ - means "$1", "$2", "$3" and "$4"
# $* - almost as same as "$@"
#
############################
# if [ ]; then
# elif [ ]; then
# else
# fi
#
############################
# case $xxx in
# "1")
#	;;
# "2")
#	;;
# "*")
#	;;
# esac
#
############################
# function xxx ()
# { }
#
############################
# while [ ]
# do
# done
#
############################
# until [ ]
# do
# done
#
############################
# for xxx in c1 c2 c3 ...
# do
# done
#
# for ((initial; limitation; step))
# do
# done
#
############################
# (( ))
# - used in "for" loop
# - used in mathematical expression, $(( )) for returning the mathematical result
# - used for local variables
#
############################
# [ ]
# - bash commands, like -b, -c, -gt, -eq, etc.
#
############################
# [[ ]]
# - an enhanced version of "[ ]"
# - support "||", "&&", reserved variables in shell, etc.
#
############################

if [[ $# -eq 2 ]] && [[ $1 -ge 0 ]] && [[ $1 =~ [0-9]+ ]]
then
	for ((i = 0; i < $1; i ++))
	do
		echo $2
	done

elif [[ $# != 2 ]]
then
	echo 'Usage: ./echon.sh <number of lines> <string>'
	exit 1

else
	echo './echon.sh: argument 1 must be a non-negative integer'
fi
