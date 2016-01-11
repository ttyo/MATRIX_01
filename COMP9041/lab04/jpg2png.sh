#!/bin/bash

ALLFILE=`ls ./`

for FILE in *
do
	NAME=`echo "$FILE" | cut -d '.' -f 1`
	EXT=`echo "$FILE" | cut -d '.' -f 2`

	if [[ "$EXT" == 'jpg' ]]
	then
		if [[ "$ALLFILE" =~ "$NAME.png" ]]
		then
			echo "$NAME.png already exists"
			exit 1
		else
			convert "$NAME.jpg" "$NAME.png"
		fi
	fi

done
	
