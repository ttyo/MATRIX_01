#!/usr/bin/perl -w

$count = 0;
$key = lc $ARGV[0];
while (<STDIN>) {
        @words = split /[^A-Za-z]/, $_;
        foreach(@words) {
                if (lc $_ eq $key) {
                        $count ++;
                }
        }
}

print "$key occurred $count times\n";


