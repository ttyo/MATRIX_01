#!/urs/bin/bash
# ran=$RANDOM
# ran=`expr $ran % 5`
ran=2
case $ran in
   0) echo "Hello";;
   1) echo "Hi";;
   2) echo "G'day";;
   3) echo "How r u";;
   *) echo "Bye";;
esac