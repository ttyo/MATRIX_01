#!/usr/bin/perl -w

sub level0 {
	print "hahah i win!\n";
}

sub level1 {
	level0();
}

sub check {
	my ($word) = @_;
	if ($word =~ /win/) {
		level1($word);
	}
}

#while (<>) {
#	($line) = $_;
#	print "$line\n";
#	$result = check($line);
#	chomp($result);
#}

while (my $line = <>) {
    my $result = '';
    open RESULT, '>', \$result or die $!;
    select RESULT;
    check($line);
    select STDOUT;
    chomp($result);
    print "$result, the result has been redirected\n";
}

