#!/usr/bin/perl -w

use CGI qw/:all/;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;
print header, start_html('Credit Card Validation');
print h2('Credit Card Validation'), "\n";
warningsToBrowser(1);

$credit_card = param('credit_card') || '';

if (defined param("value") && !defined param("close"))
{
	print p("This page checks whether a potential credit card number satisfies the Luhn Formula."), "\n";
	my $original_card = $credit_card;
	my $card = $credit_card;
	$card =~ s/\D//g; # remove non-digit things
	my $length = length($card);
	if ($length != 16)
	{
		print "<b><span style=\"color: red\">$original_card is invalid - does not contain exactly 16 digits\n</span></b><p>";
		print start_form, "\n";
		print "Try again:\n", textfield('credit_card'), "\n";
		print submit(value => Validate), "\n";
		print reset(value => Reset), "\n";
		print submit(close => Close), "\n";
		print end_form, "\n";
	}
	else
	{
		my $result = checksum($card) % 10;
		if ($result == 0)
		{
			print "<span>$original_card is valid\n</span></b><p>";
			print start_form, "\n";
			print "Another card number:\n", textfield('credit_card'), "\n";
			print submit(value => Validate), "\n";
			print reset(value => Reset), "\n";
			print submit(close => Close), "\n";
			print end_form, "\n";
		}
		else
		{
			print "<b><span style=\"color: red\">$original_card is invalid</span></b><p>\n";
			print start_form, "\n";
			print "Try again:\n", textfield('credit_card'), "\n";
			print submit(value => Validate), "\n";
			print reset(value => Reset), "\n";
			print submit(close => Close), "\n";
			print end_form, "\n";
		}
	}
}
elsif (defined param("close"))
{
	print "<span>Thank you for using the Credit Card Validator. \n</span></b><p>";
}
else
{
	print p("This page checks whether a potential credit card number satisfies the Luhn Formula."), "\n";
	print start_form, "\n";
	print "Enter credit card number:\n", textfield('credit_card'), "\n";
	print submit(value => Validate), "\n";
	print reset(value => Reset), "\n";
	print submit(close => Close), "\n";
	print end_form, "\n";
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

print end_html;
exit(0);

