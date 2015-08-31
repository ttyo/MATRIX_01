#!/bin/sh

for FILE in $@
do
	TIMESTAMP=`ls -l "$FILE" | cut -d ' ' -f 6,7,8`
	convert -gravity south -pointsize 36 -draw "text 0,10 '$TIMESTAMP'" "$FILE" temp
	mv temp $FILE
	touch -d "$TIMESTAMP" "$FILE"
done
