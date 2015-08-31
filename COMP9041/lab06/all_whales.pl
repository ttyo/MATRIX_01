#!/usr/bin/perl -w

@pod = ();
@counter = ();
@whale = ();

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
	$flag = 0;
	$i = 0;
	if ($list_size == 0) {
                push @pod, "1";
                push @counter, $number;
                push @whale, $key;
		$flag = 1;
	}
	else {
		for ($i = 0; $i < $list_size; $i ++) {
			if ($whale[$i] eq $key) {
				$pod[$i] ++;
				$counter[$i] += $number;
				$flag = 1;
				last;
			}
		}
	}
	
	if ($flag == 0) {
		push @pod, "1";
		push @counter, $number;
		push @whale, $key;
	}
}

for ($i = 0; $i < @whale; $i ++) {
	print "$whale[$i] observations: $pod[$i] pods, $counter[$i] individuals\n"
}
