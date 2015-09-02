#!/usr/bin/perl -w

$flag = 0;
@result_list1 = ();
@result_list2 = ();

if ($ARGV[0] eq "-r") {
        $flag = 1;
        &prereq($ARGV[1]);
}
else {
        &prereq($ARGV[0]);
}

@seen{@result_list1} = ();
@newresult_list = (@result_list1, grep{!exists $seen{$_}} @result_list2);
for $listed_course (sort @newresult_list) {
        print "$listed_course\n";
}

sub prereq {
        #my $course = @_; # BAD! this is not what you want!!!
        my ($course) = @_;
        my $url1 = "http://www.handbook.unsw.edu.au/postgraduate/courses/2015/$course.html";
        my $url2 = "http://www.handbook.unsw.edu.au/undergraduate/courses/2015/$course.html";
        my @pre_list1 = ();
        my @pre_list2 = ();

        open F, "wget -q -O- $url1|" or die;
        while (my $line = <F>) {
                if ($line =~ /.*Prerequisite.*/) {
                        $line =~ s/\<\/p\>\<p\>\<strong\>Excluded\:.+\<\/a\>\<\/p\>$//g;
                        #$line =~ /[A-Z]{4}[0-9]{4}/gi;
                        #@pre_list = $line; QUESTION!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        @pre_list1 = $line =~ /[A-Z]{4}[0-9]{4}/gi;

                        foreach $pre_course (@pre_list1) {
                                my $notnew = 0;
                                foreach $listed_course (@result_list1) {
                                        if ($listed_course eq $pre_course) {
                                                $notnew = 1;
                                        }
                                }
                                if ($notnew != 1) {
                                        push @result_list1, $pre_course;
                                        if ($flag == 1) {
                                                &prereq($pre_course);
                                        }
                                }
                        }
                }
        }

        open F, "wget -q -O- $url2|" or die;
        while (my $line = <F>) {
                if ($line =~ /.*Prerequisite.*/) {
                        $line =~ s/\<\/p\>\<p\>\<strong\>Excluded\:.+\<\/a\>\<\/p\>$//g;
                        @pre_list2 = $line =~ /[A-Z]{4}[0-9]{4}/gi;

                        foreach $pre_course (@pre_list2) {
                                my $notnew = 0;
                                foreach $listed_course (@result_list2) {
                                        if ($listed_course eq $pre_course) {
                                                $notnew = 1;
                                        }
                                }
                                if ($notnew != 1) {
                                        push @result_list2, $pre_course;
                                        if ($flag == 1) {
                                                &prereq($pre_course);
                                        }
                                }
                        }
                }
        }
}
