#!/usr/bin/perl -w
# 
# Author
# Chengjia Xu, CSE of UNSW
# ID: 5025306
#

@files = ();
@stdin_file = ();
$cat_lines = 10;
$stdin_lines = 0;
$stdin_flag = 0;

if (@ARGV == 0) {
	while ($input = <>) {
		push @stdin_file, $input;
	}
	$stdin_flag = 1;
}

foreach $arg (@ARGV) {
	if ($arg eq "--version") {
		print "$0: version 0.1\n";
		exit(0);
	} 
	elsif ($arg =~ /-[0-9]+/) {
		$cat_lines = $arg;
		$cat_lines =~ s/-//g;
	}
	else {
		push @files, $arg;
	}
}

if ($stdin_flag == 1) {
	$stdin_lines = $#stdin_file + 1;
	$index = 0;
	$output_lines = $cat_lines;
	$reallines = $stdin_lines;
	
	if ($reallines < $output_lines) {
                $output_lines = $reallines;
                $index = 0;
        }
        else {
                $index = $reallines - $output_lines;
        }

	$counter = 0;
	while ($counter < $output_lines) {
                $line = $stdin_file[$index];
                chomp($line);
                print "$line\n";
                $counter ++;
                $index ++;
	}
}

foreach $f (@files) {
	$index = 0;
	$output_lines = $cat_lines;
	open(F,"<$f") or die "$0: Can't open $f: $!\n";
	if (@files > 1) {
		print ("==> $f <==\n");
	}

	$getlines = `wc -l $f`;
	$reallines = (split " ", $getlines)[0];

	if ($reallines < $output_lines) {
		$output_lines = $reallines;
		$index = 0;
	}
	else {
		$index = $reallines - $output_lines;
	}

	@lines = <F>;
	$counter = 0;
	while ($counter < $output_lines) {
		$line = $lines[$index];
		chomp($line);
		print "$line\n";
		$counter ++;
		$index ++;
	}
	close(F);
}
