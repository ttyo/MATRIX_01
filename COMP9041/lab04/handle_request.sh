#!/bin/sh

# Run from webserver.sh to handle a single http request
# written by andrewt@cse.unsw.edu.au as a COMP2041 example

read http_request || exit 1

status_line="HTTP/1.0 200 OK"
content_type="text/plain"
content="Hi, I am a shell webserver and I received this HTTP request: $http_request"
REQUEST=`echo $http_request | cut -d ' ' -f 2 | tr -d ' '`

#if $("$REQUEST" | egrep ".+[A-Za-z]$")
#then
#	FILE=`echo $REQUEST | rev | cut -d '/' -f 1 | rev | tr -d "\/"`
#	file=1
#elif $("$REQUEST" | egrep ".+\/$")
#then
#	PATH=$REQUEST
#	path=1
#fi

if [[ -f ~/public_html$REQUEST ]] # REQUEST is a file
then
	NAME=`echo $REQUEST | cut -d '.' -f 1 | tr -d "\/"`
	TYPE=`echo $REQUEST | cut -d '.' -f 2`
	if [[ $TYPE == "html" ]] # is an html file
	then
		content=`cat ~/public_html$REQUEST`
		content_type="text/html"
	elif [[ $TYPE == "cgi" ]] # is a cgi file, run the script and return the running result
	then 
		TEMP=`sh ~/public_html$REQUEST`
		content=$TEMP
		content_type="text/html"
	elif [[ $(grep `echo ~/public_html$REQUEST | cut -d '.' -f 2` /etc/mime.types | cut -d '/' -f 1) == "image" ]] # is a picture
	then
		REALPATH=~/public_html$REQUEST
		content=`echo "
		<html>
		 <body>
		  <h2>$NAME</h2>
		  <img src=$REALPATH />
		 </body>
		</html>
		"`
		content_type="text/html"
	fi

elif [[ -d ~/public_html$REQUEST ]] # REQUEST is a path, search path
then
	if [[ -e ~/public_html$REQUEST/index.html ]] # path contains index.html, display index.html
	then
		content=`cat ~/public_html$REQUEST/index.html`
		content_type="text/html"
	else # path has no index.html, display directory
		REALPATH=~/public_html$REQUEST
		FILELIST=`ls -1 $REALPATH | sed "s#^.*#\<li\>\<a\ href=\"\\\\$REQUEST\/&\"\>&\<\\/a\>\<\\/li\>#" | sed 's#\/\/#\/#'`
		content=`echo "
		<html>
		  <head><title>Index of $REALPATH</title></head>
		  <body>
		    <h2>Index of $REALPATH</h2>
		    <hr>
		    <ui>
		     <li><a href="..">Parent Directory</a></li>
		     $FILELIST
		    <ui>
		  </body>
		</html>
		"`
		content_type="text/html"
	fi

else # not found
        status_line="HTTP/1.0 404 Not Found"
        content="Greetings from badass 404"
        content_type="text/html"
fi

content_length=`echo "$content"|wc -c`
echo "$status_line"
echo "Content-type: $content_type"
echo "Content-length: $content_length"
echo
echo "$content"
exit 0
