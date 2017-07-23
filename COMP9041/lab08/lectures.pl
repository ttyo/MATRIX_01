#!/usr/bin/perl -w

$human = 0;
$timetable = 0;
if ($ARGV[0] eq "-d") {
	$human = 1;
}
elsif ($ARGV[0] eq "-t") {
	$human = 1;
	$timetable = 1;
	for ($i = 0; $i < 12; $i ++) {
		for ($j = 0; $j < 5; $j ++) {
			$matrix1[${i}][${j}] = 0;
			$matrix2[${i}][${j}] = 0;
			$matrixx[${i}][${j}] = 0;
		}
	}
}

foreach $arg (@ARGV[$human .. $#ARGV]) {
	$url = "http://www.timetable.unsw.edu.au/2015/${arg}.html";
	open F, "wget -q -O- '$url'|" or die;

	while ($line = <F>) {
		if ($line =~ /\>Lecture\</i) {
			$line_index = 0;
			$finish = 0;
		}
		$line_index ++;
		if ($line_index == 2) { # teaching period
			$semester = undef;
			if ($line =~ />T[1-2]{1}</) {
				$semester = $&;
				$semester =~ s/\>//;
				$semester =~ s/\<//;
				$semester =~ s/T/S/;
			}
		}
		if ($line_index == 7) { # teaching time
			if ($line =~ />.+\)</) {
				$time = $&;
				$time =~ s/\>//;
				$time =~ s/\<//;
				
				if (!defined($semester)) {
					if (!exists($table{$arg}{X1}{$time})) {
						$table{$arg}{X1}{$time} = 1;
						$same_time = 0;
					}
					else {
						$same_time = 1;
					}
				}
				else {
					if (!exists($table{$arg}{$semester}{$time})) {
						$table{$arg}{$semester}{$time} = 1;
						$same_time = 0;
					}
					else {
						$same_time = 1;
					}
				}
				if (!$same_time && $human) {
					@details = split(/ /, $time);
					foreach $word (@details) {
						if ($word =~ /Mon|Tue|Wed|Thu|Fri/) {
							$index = 0;
							$h_finish = 0;
							$t_finish = 0;
							$date = $word;
						}
						$index ++;
						if ($index == 2) {
							$h1 = $word;
							$h1 =~ s/:[0-9]+//;
							$h1 = int($h1);
						}
						if ($index == 4) {
							@h2 = split(/:/, $word);
							$h = int($h2[0]);
							$m = int($h2[1]);
							if ($m > 0) {
								$h = $h + 1;
							}
							$duration = $h - $h1;
							$h_finish = 1;
							$t_finish = 1;
						}
						if($h_finish && !$timetable) {
							for ($i = 0; $i < $duration; $i ++) {
								if (!defined($semester)) {
									print "X1 $arg $date"
								}
								else {
									print "$semester $arg $date"
								}
								$print_time = $h1 + $i;
								print " $print_time";
								print "\n";
							}
							$h_finish = 0;
						}
						if ($t_finish && $timetable) {
							if (lc $date eq "mon") {
								$index2 = 0;
							}
							elsif (lc $date eq "tue") {
								$index2 = 1;
							}
							elsif (lc $date eq "wed") {
								$index2 = 2;
							}
							elsif (lc $date eq "thu") {
								$index2 = 3;
							}
							elsif (lc $date eq "fri") {
								$index2 = 4;
							}
							if (lc $semester eq "s1") {
								$matrix1_changed = 1;
								for ($n = 0; $n < $duration; $n ++) {
									$index1 = $h1 + $n - 9;
									$matrix1[$index1][$index2] ++;
								}
							}
							elsif (lc $semester eq "s2") {
								$matrix2_changed = 1;
								for ($n = 0; $n < $duration; $n ++) {
									$index1 = $h1 + $n - 9;
									$matrix2[$index1][$index2] ++;
								}
							}
							elsif (!defined($semester)) {
								$matrixx_changed = 1;
								for ($n = 0; $n < $duration; $n ++) {
									$index1 = $h1 + $n - 9;
									$matrixx[$index1][$index2] ++;
								}
							}
							$t_finish = 0;
						}
					}
				}
				$finish = 1;
			}
		}
		if ($finish && !$timetable && !$same_time) {
			if (!$human) {
				if (!defined($semester)) {
					print "$arg: X1 $time\n";
				}
				else {
					print "$arg: $semester $time\n";
				}
				$finish = 0;
			}
		}
	}
}
if ($timetable) {
	if ($matrix1_changed) {
		print "S1       Mon   Tue   Wed   Thu   Fri\n";
		for ($i = 0; $i < 12; $i ++) {
			$label = $i + 9;
			$label =~ s/^[9]$/09/;
			$label = "${label}:00";
			print "$label";
			for ($j = 0; $j < 5; $j ++) {
				if ($matrix1[${i}][${j}] == 0) {
					print "      ";
				}
				else {
					print "     $matrix1[${i}][${j}]";
				}
			}
			print "\n";
		}
	}
	if ($matrix2_changed) {
		print "S2       Mon   Tue   Wed   Thu   Fri\n";
		for ($i = 0; $i < 12; $i ++) {
			$label = $i + 9;
			$label =~ s/^[9]$/09/;
			$label = "${label}:00";
			print "$label";
			for ($j = 0; $j < 5; $j ++) {
				if ($matrix2[${i}][${j}] == 0) {
					print "      ";
				}
				else {
					print "     $matrix2[${i}][${j}]";
				}
			}
			print "\n";
		}
	}
	if ($matrixx_changed) {
		print "X1       Mon   Tue   Wed   Thu   Fri\n";
		for ($i = 0; $i < 12; $i ++) {
			$label = $i + 9;
			$label =~ s/^[9]$/09/;
			$label = "${label}:00";
			print "$label";
			for ($j = 0; $j < 5; $j ++) {
				if ($matrixx[${i}][${j}] == 0) {
					print "      ";
				}
				else {
					print "     $matrixx[${i}][${j}]";
				}
			}
			print "\n";
		}
	}
}

