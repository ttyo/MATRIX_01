#!/usr/bin/perl -w

for my $card (@ARGV)
{
	my $original_card = $card;
	$card =~ s/\D//g; # remove non-digit things
	my $length = length($card);
	if ($length != 16)
	{
		print "$original_card is invalid - does not contain exactly 16 digits\n";
	}
	else
	{
		my $result = checksum($card) % 10;
		if ($result == 0)
		{
			print "$original_card is valid\n";
		}
		else
		{
			print "$original_card is invalid\n";
		}
	}
}

sub checksum
{
	my ($card) = @_;
	my $checksum = 0;
	my $index = 0;
	for ($index = 15; $index >= 0; $index --) 
	{
		my $digit = substr $card, $index, 1;
		my $multiplier = 1 + (15 - $index) % 2;
		my $d = int($digit) * $multiplier;
		if ($d > 9)
		{
			$d = $d - 9;
		}
		$checksum = $checksum + $d;
	}
	return $checksum;
}

