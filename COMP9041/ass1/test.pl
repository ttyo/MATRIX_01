#!/usr/bin/perl -w

$string = '$abc$efg';
@result = split /\$/, $string;

foreach $doh (@result) {
	print "###$doh\n";
}
