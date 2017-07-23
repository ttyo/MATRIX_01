#!/usr/bin/perl -w

@pod = ();
@counter = ();
@whale = ();
@result_list = ();

while (my $line = <STDIN>) {
	chomp($line);
	$line =~ s/ +/ /g;
	$line =~ s/ +$//g;
	@line_split = split / /, $line, 2;
	$number = $line_split[0];
	$key_raw = $line_split[1];

	$key_raw_lc = lc $key_raw;
	if ($key_raw_lc =~ /.+s$/) {
		$key_raw_lc_singular = substr($key_raw_lc, 0, -1);
		$key = $key_raw_lc_singular;
	}
	else {
		$key = $key_raw_lc;
	}

	$list_size = @whale;
	$notnew = 0;
	if ($list_size == 0) {
                push @pod, "1";
                push @counter, $number;
                push @whale, $key;
		$notnew = 1;
	}
	else {
		for ($i = 0; $i < $list_size; $i ++) {
			if ($whale[$i] eq $key) {
				$pod[$i] ++;
				$counter[$i] += $number;
				$notnew = 1;
				last;
			}
		}
	}
	
	if ($notnew == 0) {
		push @pod, "1";
		push @counter, $number;
		push @whale, $key;
	}
}

for ($i = 0; $i < @whale; $i ++) {
	$result = "$whale[$i] observations: $pod[$i] pods, $counter[$i] individuals\n";
	push @result_list, $result;
}

@sorted_result = sort @result_list;
for ($i = 0; $i < @whale; $i ++) {
	print $sorted_result[$i];
}
