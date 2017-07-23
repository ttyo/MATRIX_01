#!/usr/bin/perl -w

$count = 0;
while (<STDIN>) {
	@words = split /[^A-Za-z]/, $_;
	foreach(@words) {
		if (!($_ =~ /^$/)) {
			$count ++;		
		}
	}
}

print "$count words\n";
