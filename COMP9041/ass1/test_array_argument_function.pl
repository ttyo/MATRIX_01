#!/usr/bin/perl -w

@t = ("this", "is", "a", "test");
test(\@t, 1);

sub test {
	my ($array, $tab, $if) = @_;
	@result = @$array;
	foreach $str (@result){
		print "$str\n";
	}
	print "$tab\n";
}

$str = "this is a test2";
test2($str, 1, 9);

sub test2 {
	my ($a, $b, $c) = @_;
	print "$a\n";
	print "$b\n";
	print "$c\n";
}




