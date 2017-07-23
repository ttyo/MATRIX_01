#!/usr/bin/perl
print "
*******************************auto test*******************************
---There are some test cases for comp9041/2041 assignment 1.
---Lv0 - Lv4 are the examples which are downloaded on the assignment
   requirement webpage.
---Extended test cases are some functions which are required but not
   exist in the examples
                                      \@Created by Leo on 2015/9/20.
***********************************************************************
Press y/n to continue, good luck!!!!!!
y/n  ";
while(<STDIN>){
	$_ =~ tr/[A_Z]/[a_z]/;
	$_ =~ s/\n//g;
	if($_ eq "y"){
		last;
	}else{
		exit(0);
	}
}

if(-e "shpy.pl"){
}else{
	print "ERROR : Can not find shpy.pl\n";
	exit(0);
}


for(my $i = 0; $i <= 5; $i++){
	if($i eq 5){
		print "\n              extended test cases                 \n";
	}else{
		print "\n                  LV $i                 \n";
	}
	
	foreach $file (glob "examples/$i/*.sh") {
		$args = "";
		if($file eq "examples/2/args.sh"){
			$args = "a b c d e";
		}elsif($file eq "examples/3/l.sh"){
			$args = "*.py *.sh *.pl";
		}elsif($file eq "examples/3/sequence0.sh"){
			$args = "1 6";
		}elsif($file eq "examples/4/sequence1.sh"){
			$args = "1 10";
		}elsif($file eq "examples/1/for_read0.sh"){
			next;
		}elsif($file eq "examples/5/long.sh"){
			$args = "1 10";
		}elsif($file eq "examples/5/echo6.sh"){
			$args = "1 2 3 4 5";
		}

		
		print "test $file...................";
		system("./shpy.pl $file > result.py" );
		initFiles();
		system("bash $file > sh.output $args");
		initFiles();
		system("python result.py 1> py.output 2>py.output $args");
		if(system("diff -y -W 60 sh.output py.output > differences") == 0){
			print "passed\n";
		}else{
			print "failed\n------------sh------------------------python----------------\n";
			system("cat differences");
		}
	}
}

sub initFiles{
	system("rm -f 111");
	system("touch 1");
	system("rm -f 777");
	system("touch 777");
	system("touch xxx");
}





# print "-----------------------python output-----------------------\n";
# system("python ./test.py 1 2 3 4 5" );
# print "-----------------------bash   output-----------------------\n";
# system("bash ./test.sh 1 2 3 4 5" ) ;
# print "-----------------------compare result----------------------\n";
# system("rm rePython");
# system("rm reBash");
# system("rm differences");
# system("python ./test.py 1 2 3 4 5 >> rePython" );
# system("bash ./test.sh 1 2 3 4 5 >> reBash" );
# if(system("diff -y -W 60 rePython reBash >> differences") == 0){
# 	print "passed\n";
# }else{
# 	system("cat differences");
# 	print "failed\n";
# }