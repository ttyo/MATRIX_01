#!/usr/bin/perl -w

$counter = 0;
while(<>) {
	$line = $_;
	chomp($line);
	push(@all, $line);
	$counter ++;
}

$i = 0;
while ($i < $counter) {
	$index = rand($counter);
		if ($all[$index] ne "N/A") { ### do not use "!=", use "ne" (not equal)
		print "$all[$index]\n";
		$all[$index] = "N/A";
		$i ++;
	}
}
