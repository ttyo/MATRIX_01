
# test command
#
# test (-n) STRING
# test whether the STRING is null, if null then return 0, else return 1, "-n" is not necessary
#
# test -z STRING
# test whether the STRING is not null, if not null then return 0, else return 1
#
# test -r | -w | -x FILE
# test whether the FILE is readable/writable/executable
#
# test -nt | -ot FILE1 FILE2
# test whether FILE1 is newer/older than FILE2
#
# test -eq | -ne | -gt | -lt | -ge | -le NUM1 NUM2
# test whether NUM1 is equal/not equal/greater/less/greater or equal/less or equal to NUM2
#

#!/bin/bash

for FILE in "$@"
do
	read -p "Address to e-mail this image to? " ADDRESS
	if test $ADDRESS
	then
		read -p "Message to accompany image? " MESSAGE
		echo "$MESSAGE" | mutt -s "Greeting from week04" -a "$FILE" -- "$ADDRESS"
		echo "$FILE sent to $ADDRESS"
	fi
done

	
