#!/usr/bin/perl -w

if ($#ARGV != 1) {
	print "Usage: ./echon.pl <number of lines> <string>\n";
	exit 1;
}

$number = $ARGV[0];
$string = $ARGV[1];
for ($i = 0; $i < $number; $i ++) {
	print "$string\n";
}
