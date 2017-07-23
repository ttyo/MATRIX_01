#!/usr/bin/perl -w

$debug = 0;
foreach $arg (@ARGV) {
	if ($arg eq "-d") {
		$debug = 1;
	}
	elsif ($arg eq "poem?.txt") {
		opendir(DIR, ".") or die "Could not open current directory\n";
		while (my $poem = readdir(DIR)) {
			if ($poem =~ /poem[0-9]+.txt/){
				push (@input, $poem);
			}
		}
		@input = sort @input;
	}
	else {
		push (@input, $arg);
	}
}

sub hashValueDescendingNum {
	$result{$b} <=> $result{$a};
}

#opendir(DIR, ".") or die "Could not open current directory\n";
#while (my $poem = readdir(DIR)) {
#	if ($poem ~~ @input) {
foreach my $poem (@input) {
		open (PM, "<$poem") or die "Cannot open file $poem\n";
		@poemwordslist = ();
		while (<PM>) {
			my @wordspm = split /[^A-Za-z]/, $_;
			foreach my $word (@wordspm) {
				$word = lc $word;
				if (!($word =~ /^$/)) {
					push (@poemwordslist, $word);
				}
			}
		}

		%result = ();
		%table = ();
		@poetlist = ();
		foreach my $poet (glob "poets/*.txt") {
			$total = 0;
			open (PT, "<$poet") or die "Cannot open file $poet\n";
			$poet =~ s/poets\///;
			$poet =~ s/\.txt//;
			$poet =~ tr/_/ /;
			$result{$poet} = 0;
			push (@poetlist, $poet);

			while (<PT>) {
				my @wordspt = split /[^A-Za-z]/, $_;
				foreach my $word (@wordspt) {
					$word = lc $word;
					if (!($word =~ /^$/)) {
						$total ++;
					}
					if (!exists ($table{$poet}{$word})) {
						$table{$poet}{$word} = 1;
					}
					else {
						$table{$poet}{$word} ++;
					}
				}
			}
			$table{$poet}{"total_words"} = $total;
		}
		
		foreach my $wordpm (@poemwordslist) {
			foreach my $poet (@poetlist) {
				if (!exists ($table{$poet}{$wordpm})) {
					$result{$poet} = $result{$poet} + log(0 + 1 / $table{$poet}{"total_words"});
				}
				else {
					$result{$poet} = $result{$poet} + log(($table{$poet}{$wordpm} + 1) / $table{$poet}{"total_words"});
				}
			}
		}
                if ($debug == 1) {
                        foreach $key (sort hashValueDescendingNum (keys %result)) {
				printf "%s: log_probability of %5.1f for %s\n", $poem, $result{$key}, $key;
                        }
                        my $firstkey = (sort hashValueDescendingNum (keys %result))[0];
                	printf "%s most resembles the work of %s (log-probability=%5.1f)\n", $poem, $firstkey, $result{$firstkey};
                }
                else {
                        my $firstkey = (sort hashValueDescendingNum (keys %result))[0];
			printf "%s most resembles the work of %s (log-probability=%5.1f)\n", $poem, $firstkey, $result{$firstkey};
                }
#	}
}

#closedir(DIR);

