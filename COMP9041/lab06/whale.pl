#!/usr/bin/perl -w

if (@ARGV == 1) {
	$pod = 0;
	$counter = 0;
	$keyline = $ARGV[0];
	chomp($keyline);

	while (my $line = <STDIN>) {
		chomp($line);
		@line_split = split / /, $line, 2;
		$number = $line_split[0];
		$key = $line_split[1];
		if ($key eq $keyline) {
			$pod ++;
			$counter += $number;
		}
	}
	print "$keyline observations: $pod pods, $counter individuals\n"
}
