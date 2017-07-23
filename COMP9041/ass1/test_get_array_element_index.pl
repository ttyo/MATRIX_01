#!/usr/bin/perl -w

@strings = (
	"this",
	"is",
	"a",
	"test",
	"new1",
	"hahaha",
	"I",
	"won",
	"new2",
	"blah",
	"blah",
	);


sub get_index {
	while (@_) {
		return @_-1 if $_[0] eq pop
	}
}

@s1;
@s2;
@s3;

foreach $word (@strings) {
	if ($word !~ /new/) {
		push @s1, $word;
	elsif ($word =~ /new1/){
		$index = get_index($word, @strings);
		$word = $strings[index - 1]		
}
