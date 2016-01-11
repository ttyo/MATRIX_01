#!/bin/sh

echo Content-type: text/html
echo

host_address=`host $REMOTE_ADDR 2>&1|grep Name|sed 's/.*: *//'`
LOCAL_HOSTNAME=`host $REMOTE_ADDR|sed 's/^.*pointer //'|sed 's/\.$//'`


cat <<eof
<!DOCTYPE html>
<html lang="en">
<head>
<title>Webserver IP, Host and Software</title>

</head>
<body>

Your browser is running at IP address: <b>$REMOTE_ADDR</b>
<p>
Your browser is running on hostname: <b>$LOCAL_HOSTNAME</b>
<p>
Your browser identifies as: <b>$HTTP_USER_AGENT</b>

</body>
</html>
eof


