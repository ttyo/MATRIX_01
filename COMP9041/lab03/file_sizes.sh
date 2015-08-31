#!/bin/bash
# 
# Author
# Chengjia Xu, CSE of UNSW
# ID: 5025306
#
#####################################
# about the "whitespace" around "=" #
#####################################
# STR = 'fool'
#
# bash tries to run a sommand named STR with 2 arguments (that is '=' and 
# 'fool')
# equivalent to: STR '=' 'fool'
#
##########################
# STR ='fool'
# 
# bash tries to run a command named STR with 1 argument (that is '=fool')
# equivalent to: STR '=fool'
##########################
#
# STR= 'foo'
#
# bash tries to run the command 'fool' with STR set to the empty string in 
# its environment
# equivalent to: STR='' foo
#
##########################

BASEDIR=$(pwd)
FILES=$BASEDIR/*

smallfiles=''
mediumfiles=''
largefiles=''

for file in $FILES
do
	if [[ `wc -l < "$file"` -lt 10 ]]
	then
		small_files="$small_files $file"
	elif [[ `wc -l < "$file"` -lt 100 ]]
	then
		medium_files="$medium_files $file"
	else
		large_files="$large_files $file"
	fi
done

small_files=${small_files//"$BASEDIR/"/''}
medium_files=${medium_files//"$BASEDIR/"/''}
large_files=${large_files//"$BASEDIR/"/''}
echo "Small files:$small_files"
echo "Medium-sized files:$medium_files"
echo "Large files:$large_files"
