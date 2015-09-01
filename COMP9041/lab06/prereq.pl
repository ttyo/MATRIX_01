#!/usr/bin/perl -w

$flag = 0;
if ($ARGV[0] eq "-r") {
        $flag = 1;
        &prereq($ARGV[1]);
}
else {
        &prereq($ARGV[0]);
}

sub prereq {
        #my $course = @_; # BAD! this is not what you want!!!
        my ($course) = @_;
        $url1 = "http://www.handbook.unsw.edu.au/postgraduate/courses/2015/$course.html";
        $url2 = "http://www.handbook.unsw.edu.au/undergraduate/courses/2015/$course.html";
        @pre_list = ();
        
        open F, "wget -q -O- $url1 $ url2|" or die;
        while ($line = <F>) {
                if ($line =~ /.*Prerequisite:.*/) {
                        $line =~ s/\<\/p\>\<p\>\<strong\>Excluded\:.+\<\/a\>\<\/p\>$//g;
                        #$line =~ /[A-Z]{4}[0-9]{4}/gi;
                        #@pre_list = $line; QUESTION!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        @pre_list = $line =~ /[A-Z]{4}[0-9]{4}/gi;
                        for $pre (@pre_list) {
                                print "$pre\n";
                        }
                }
        }
}
