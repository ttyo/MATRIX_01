#!/usr/bin/perl -w

$key = lc $ARGV[0];

foreach $file (glob "poets/*.txt") {
	$total = 0;
	$key_total = 0;
	open (F, "<$file") or die "Cannot open file $file\n";
	while (<F>) {
        	@words = split /[^A-Za-z]/, $_;
		foreach(@words) {
                	if (lc $_ eq $key) {
			$key_total ++;
                	}
                	if (!($_ =~ /^$/)) {
                        	$total ++;
			}
        	}
	}

	$file =~ s/poets\///;
	$file =~ s/\.txt//;
	$file =~ tr/_/ /;
	$table{$file} = $total;
	$table{$file}{$key} = $key_total;
}

#$size = keys %table;
foreach $poet (sort keys %table) {
	printf "%4d/%6d = %.9f %s\n", $table{$poet}{$key}, $table{$poet}, $table{$poet}{$key}/$table{$poet}, $poet;
}


