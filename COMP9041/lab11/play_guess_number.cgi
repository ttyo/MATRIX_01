#!/usr/bin/perl -w
# Simple CGI script written by andrewt@cse.unsw.edu.au
# Outputs a form which will rerun the script
# An input field of type hidden is used to pass an integer
# to successive invocations
# Two submit buttons are used to produce different actions

use CGI qw/:all/;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);

print <<eof;
Content-Type: text/html

<!DOCTYPE html>
<html lang="en">
<head>
    <title>Handling Multiple Submit Buttons</title>
</head>
<body>
eof
warningsToBrowser(1);

$result = param("x") || 50;
$lower = param('l') || 1;
$higher = param('h') || 100;
$new = 0;

if (defined param("higher") && !defined param('correct'))
{
	$lower = $result;
	$result = int($result + ($higher - $result) / 2);
}
elsif (defined param("lower") && !defined param('correct'))
{
	$higher = $result;
	$result = int($result - ($result - $lower) / 2);
}
if (defined param('correct'))
{
	print "I win!!!!";
	$new = 1;
}

if (!defined param('correct') && !$new)
{
print <<eof;
<h2>I want to play a game ... oooh hahahahaha</h2>
<form method="post" action="">
My guess is: $result
<input type=hidden name="x" value="$result">
<input type=hidden name="l" value="$lower">
<input type=hidden name="h" value="$higher">
<input type="submit" name="higher" value="Higher?">
<input type="submit" name="correct" value="Correct?">
<input type="submit" name="lower" value="Lower?">
</form>
</body>
</html>
eof
}

if ($new)
{
$new = 0;
print <<eof;
<form method="post" action="">
<input type="submit" name="again" value="Play Again">
</form>
</body>
</html>
eof
}
