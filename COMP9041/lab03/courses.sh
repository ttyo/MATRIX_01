#!/bin/bash
# 
# Author
# Chengjia Xu, CSE of UNSW
# ID: 5025306
#

wget -q -O- "http://www.handbook.unsw.edu.au/vbook2015/brCoursesByAtoZ.jsp?StudyLevel=Undergraduate&descr=$1" | egrep "[A-Z]{4}[0-9]{4}.html" | egrep "$1" | cut -d '<' -f 3 | cut -d "\"" -f 2,3 | sed s/'http:\/\/www.handbook.unsw.edu.au\/undergraduate\/courses\/2015\/'//g | sed s/'\.html\">'/' '/g | sort | uniq > under_G
wget -q -O- "http://www.handbook.unsw.edu.au/vbook2015/brCoursesByAtoZ.jsp?StudyLevel=Postgraduate&descr=$1" | egrep "[A-Z]{4}[0-9]{4}.html" | egrep "$1" | cut -d '<' -f 3 | cut -d "\"" -f 2,3 | sed s/'http:\/\/www.handbook.unsw.edu.au\/postgraduate\/courses\/2015\/'//g | sed s/'\.html\">'/' '/g | sort | uniq > post_G

cat under_G > all_G
cat post_G >> all_G

newline=false
for course in "`sort < all_G | sed 's/[ \t]$//g' | uniq`"
do
        if [[ !("$newline") ]]
        then
                echo -ne "$course"
                newline=true
        else
                echo -ne "$course\n"
                newline=false
        fi
done
