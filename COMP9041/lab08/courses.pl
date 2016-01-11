#!/usr/bin/perl -w

$key = $ARGV[0];
$url = "http://www.timetable.unsw.edu.au/2015/${key}KENS.html";

open F, "wget -q -O- '$url'|" or die;
while ($line = <F>) {
	if ($line =~ /\>[A-Z]{4}[0-9]{4}\</i) {
		$course = $&;
		$course =~ s/\>//;
		$course =~ s/\<//;
		print "$course\n";
	}
}
