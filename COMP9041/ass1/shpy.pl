#!/usr/bin/perl -w
#
# Assignment 1 of COMP2041/9041
# A translator in Perl, in order to translate shell script into the way of Python (2.7)
# Author: Chengjia Xu, 5025306, CSE of UNSW
# Sept, 2015
#
#

push @level0_single_command_list, '\bls\b';
push @level0_single_command_list, '\bpwd\b';
push @level0_single_command_list, '\bid\b';
push @level0_single_command_list, '\bdate\b';
push @level0_single_command_list, '\brm\b';
push @level0_single_command_list, '\bmv\b';
push @level0_translate_command_list, '\bexit\b';
push @level0_translate_command_list, '\bread ';
push @level0_translate_command_list, '\bcd\b';
push @level0_translate_command_list, '\btest ';
push @level0_translate_command_list, '\bexpr ';
push @level0_translate_command_list, '\becho ';
push @loop_key_words, '\bfor ';
push @loop_key_words, '\bwhile ';
#push @loop_key_words, '\bdo\b';
#push @loop_key_words, '\bdone\b';
push @if_key_words, '\bif ';
push @if_key_words, '\belse\b';
push @if_key_words, '\belif ';
#push @if_key_words, '\bthen\b';
#push @if_key_words, '\bfi\b';

$table_privilege{"rwx"} = 7; # read, write and execute
$table_privilege{"rw-"} = 6; # read and write
$table_privilege{"r-x"} = 5; # read and execute
$table_privilege{"r--"} = 4; # read only
$table_privilege{"-wx"} = 3; # write and execute
$table_privilege{"-w-"} = 2; # write only
$table_privilege{"--x"} = 1; # execute only
$table_privilege{"---"} = 0; # none
$table_privilege{7} = "rwx";
$table_privilege{6} = "rw-";
$table_privilege{5} = "r-x";
$table_privilege{4} = "r--";
$table_privilege{3} = "-wx";
$table_privilege{2} = "-w-";
$table_privilege{1} = "--x";
$table_privilege{0} = "---";

# used for a quicker key-word search
$search_in_single_commands = join("|", @level0_single_command_list);
$search_in_translate_commands = join("|", @level0_translate_command_list);
$search_in_loop_key_words = join("|", @loop_key_words);
$search_in_if_key_words = join("|", @if_key_words);

while ($line = <>) {
	chomp($line);
	push @input_lines, $line;
}

$in_for_loop = 0;
$in_while_loop = 0;
$in_if_condition = 0;
$in_case = 0;
@for_loop_stack = ();
@while_loop_stack = ();
@if_condition_stack = ();
@case_esac_stack = ();
@case_function = ();
@case_choice = ();
$case_counter = 0;
$function_counter = 0;
%variable_type = ();

###################################################################
#								  #
# 			functional functions 			  #
#								  #
###################################################################
#
# check imported libraries and display them firstly
#
sub check_import_libraries {
	my @import_list;
	foreach my $line (@input_lines) {
		if ($line =~ /$search_in_single_commands|\brm\b|\btrue\b|\bfgrep\b/) {
			if (!("import subprocess\n" ~~ @import_list)) {
				push @import_list, "import subprocess\n";
			}
		}
		if ($line =~ /\-d {1}|\-a {1}|\-f {1}/) {
			if (!("import os.path\n" ~~ @import_list)) {
				push @import_list, "import os.path\n";
			}
		}
		if ($line =~ /\bcd\b|\-r {1}|\brm\b|\bchmod\b/) {
			if (!("import os\n" ~~ @import_list)) {
				push @import_list, "import os\n";
			}
		}
		if ($line =~ /exit|read|\$[0-9]+|\$\@|\$\#/) {
			if (!("import sys\n" ~~ @import_list)) {
				push @import_list, "import sys\n";
			}
		}
		if ($line =~ /\*\.[A-Za-z]+/) {
			if (!("import glob\n" ~~ @import_list)) {
				push @import_list, "import glob\n";
			}
		}
		#if ($line =~ /\brm\b/ && $line =~ /\-rf|\-r|\-fr/) {
		#	if (!("import shutil\n" ~~ @import_list)) {
		#		push @import_list, "import shutil\n";
		#	}
		#}
		#if ($line =~ /\bchmod\b/) {
		#	if (!("import start\n" ~~ @import_list)) {
		#		push @import_list, "import start\n";
		#	}
		#}
	}
	print @import_list;
}

#
# get index of a specific $line from the @array
#
sub get_index {
	while (@_) {
		return @_-1 if $_[0] eq pop
	}
}

#
# count the spaces in front of the string ($tabs)
#
sub count_leading_spaces {
	my ($line) = @_;
	my @string = split(/\s/, $line);
	my $number_of_tabs = 0;
	my $size = @string;
	my $stop_loop = 0;
	for (my $count = 0; $count < $size; $count++) {
		if($stop_loop == 0) {
			if($string[$count] =~ /([A-Za-z0-9@])/) {
					$stop_loop = 1;
			}
			else {
				++ $number_of_tabs;
			}
		}
	}

	# make sure that the number of tabs is 4 * n, where n = 0, 1, 2, 3...
	if ($number_of_tabs % 4 != 0) { 
		my $devider = int($number_of_tabs / 4);
		my $remainder = $number_of_tabs % 4;
		if ($remainder <= 2) {
			$number_of_tabs = 4 * $devider;
		}
		elsif ($remainder > 2) {
			$number_of_tabs = 4 * ($devider + 1);
		}
	}
	return $number_of_tabs;
}

#
# convert variable's type tag, from int to string, string to int
#
sub convert_type { 
	my ($variable) = @_;
	if (exists($variable_type{$variable})) {
		if ($variable_type{$variable} eq "int") {
			$variable_type{$variable} = "string";
		}
		elsif ($variable_type{$variable} eq "string") {
			$variable_type{$variable} = "int";
		}
	}
}

###################################################################
#								  #
# 			  level 0 functions 			  #
#								  #
###################################################################

######################## level 0 / level 1 / level 2 / level 3 / level 4
# handle_echo
# this subroutine will handle simple echo command
# including redirect, double quotes, single quotes, variables, system variables, option n
########################
sub handle_echo {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp($line);
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}
	
	$line =~ s/^ +//;
	$line =~ s/ +$//;
	my @words = split / /, $line;
	
	# condition of redirect
	my $index = 1;
	my $option_n = 0;
	if ($line =~ />>/) { 
		$line =~ s/ +//g;
		my @words_2 = split />>/, $line;
		my $variable = $words_2[0];
		my $file = $words_2[1];
		$variable =~ s/^echo//;
		$variable =~ s/^\$//;
		$file =~ s/^\$//;
		print "with open($file, 'a') as f: print >>f, $variable";
		if (!$isif && !$iscomment && !$iswhile) {
			print "\n";
		}
	}

	# condition of echo, with/without option n, with/without trailing newline
	else {
		if ($words[1] eq '-n') {
			$index = 2;
			$option_n = 1;
		}

		# if the echo content has double quotes
		if ($words[$index] =~ /\".+/) {
			print "print";

			# if there is only one word
			if ($index == $#words) {
				my $word = $words[$index];
				$word =~ s/ +//g;

				# if the single word is a variable
				if ($word =~ /^\"\$/) {
					my @variable_words = split /\$/, $word;
					$variable_words[1] = handle_variable("\$$variable_words[1]", 0, 0, 0, 0);
					print " $variable_words[1]";
					
					foreach my $variable (@variable_words[2 .. $#variable_words]) {
						$variable = handle_variable("\$$variable", 0, 0, 0, 0);
						print " + $variable";
					}
				}
				
				# if the single word contains a variable
				elsif ($word =~ /.+\$/) {
					my @subwords = split /\$/, $word;
					my $string = "$subwords[0]\"";
					my $variable = "\$$subwords[1]";
					$string = handle_variable($string, 0, 0, 0, 0);
					$variable = handle_variable($variable, 0, 0, 0, 0);
					print " $string + $variable";
				}

				# if the single word is not a variable
				else {
					print " $word"
				}
			}

			# if there are many words in echo
			else {
				foreach my $word (@words[$index .. $#words]) {
					my $current_index = get_index($word, @words);

					# if current word is a variable
					if ($word =~ /^\$|\"\$/) {
						$word =~ s/\"//g;
						my @variable_words = split /\$/, $word;
						my $variable = $variable_words[1];
						$variable = handle_variable("\$$variable", 0, 0, 0, 0);
						print " $variable";
					
						foreach my $variable (@variable_words[2 .. $#variable_words]) {
							$variable = handle_variable("\$$variable", 0, 0, 0, 0);
							print " + $variable";
						}

						if ($current_index !~ $#words) {
							$words[$current_index + 1] = "\"$words[$current_index + 1]";
							print ",";
						}
					}

					# if next one is a variable
					elsif (($current_index != $#words) && $words[$current_index + 1] =~ /^\$/) {
						$word = handle_variable("$word\"", 0, 0, 0, 0);
						print " $word,";
					}
					else {
						$word = handle_variable($word, 0, 0, 0, 0);
						print " $word";
					}
				}
			}
		}

		# if the echo content has single quotes
		elsif ($words[$index] =~ /\'.+/) {
			print "print";
			foreach my $word (@words[$index .. $#words]) {
				print " $word";
			}
		}

		# if the echo content has no quotes
		else {
			print "print";

			# if there is only one word
			if ($index == $#words) {
				my $word = $words[$index];
				$word =~ s/ +//g;

				# if the single word is a variable
				if ($word =~ /^\$/) {
					my @variable_words = split /\$/, $word;
					$variable_words[1] = handle_variable("\$$variable_words[1]", 0, 0, 0, 0);
					print " $variable_words[1]";
					
					foreach my $variable (@variable_words[2 .. $#variable_words]) {
						$variable = handle_variable("\$$variable", 0, 0, 0, 0);
						print " + $variable";
					}
				}
				
				# if the single word contains a variable
				elsif ($word =~ /.+\$/) {
					my @subwords = split /\$/, $word;
					my $string = "\'$subwords[0]\'";
					my $variable = "\$$subwords[1]";
					$string = handle_variable($string, 0, 0);
					$variable = handle_variable($variable, 0, 0);
					print " $string + $variable";
				}

				# if the single word is not a variable
				else {
					print " \'$word\'"
				}
			}

			else {

				# if there are many words in echo
				my $first = $words[$index];
				foreach my $word (@words[$index .. $#words]) {
					my $current_index = get_index($word, @words);
					if ($first ne $word) {
						print ",";
					}

					# if current word is a variable
					if ($word =~ /^\$/) {
						my @variable_words = split /\$/, $word;
						my $variable = $variable_words[1];
						$variable = handle_variable("\$$variable", 0, 0, 0, 0);
						print " $variable";
					
						foreach my $variable (@variable_words[2 .. $#variable_words]) {
							$variable = handle_variable("\$$variable", 0, 0, 0, 0);
							print " + $variable";
						}
					}
					
					# if current word is not a variable
					else {
						$word = handle_variable($word, 0, 0, 0, 0);
						print " \'$word\'";
					}
				}
			}
		}
		if ($option_n) {
			print ",";
		}
		if (!$isif && !$iscomment && !$iswhile) {
			print "\n";
		}
	}
}

######################## level 0 / level 3 / level 4
# handle_simple_command
# simple commands including boolean which no need to be translated are all in here, e.g., ls, pwd, mv
########################
sub handle_simple_command {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp($line);
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}

	my $isend = 0;
	my $isrm = 0;
	my $rmoption = 0;
	my @words = split / /, $line;

	# if the first word is boolean or a string (command itself)
	if ($words[0] =~ /\btrue\b/) {
		print "not subprocess.call([\'$words[0]\'])";
		$isend = 1;
	}
	elsif ($words[0] =~ /\bfalse\b/) {
		print "not subprocess.call([\'$words[0]\'])";
		$isend = 1;
	}

	# I did not read the description carefully, was trying to translate rm command into a python way (os.remove)
	#
	# if the command is rm
	#elsif ($words[0] =~ /\brm\b/) {
	#
	#	# remove a directory
	#	if ($words[1] =~ /\-rf|\-r/) {
	#		print "shutil.rmtree(";
	#		$rmoption = 1;
	#	}
	#
	#	# remove a file
	#	else {
	#		print "os.remove(";
	#	}
	#	$isrm = 1;
	#}

	# rest of the simple commands, like mv, ls
	else {
		print "subprocess.call([\'$words[0]\'";	
	}


	# handle rm, rm command comes with three or two words, e.g., rm xxx or rm <option> xxx
	#if ($isrm) {
	#	my $rmindex = 1;
	#	# rm command with option, remove directory
	#	if ($rmoption) {
	#		$rmindex = 2;
	#	}
	#
	#	if ($words[$rmindex] !~ /\$/) {
	#		print "\'$words[$rmindex]\')";
	#	}
	#	else {
	#		$words[$rmindex] = handle_variable($words[$rmindex], 0, 0, 0);
	#		print "$words[$rmindex])";
	#	}
	#	$isend = 1;
	#}

	# if not rm command, then loop in the rest of the words
	#else {
		foreach my $word (@words[1 .. $#words]) {

			# word is not a variable
			if ($word !~ /\$/) {
				print ", ";
				print "\'$word\'";
			}

			# $word is a variable
			else {

				# word is a normal variable (not system variables)
				if ($word =~ /\$[^\@\#\$\%\&\*]/) {
					$word = handle_variable($word, 0, 0, 0);
					print ", ";
					print "str($word)";
				}

				# word is a system variable
				else {
					$word = handle_variable($word, 0, 0, 0);
					print "] + ";
					print "$word";
					print ")";
					$isend = 1;
				}
			}
		}
	#}
	if (!$isend) {
		if ($words[0] =~ /\bmv\b/) {
			print "], shell = True)";
		}
		else {
			print "])";
		}
	}
	if (!$isif && !$iscomment && !$iswhile) {
		print "\n";
	}
}

######################## level 0 / level 3
# handle_equation
# match any equations like xxxx = xxxx
# in here the type of a varibale will be defined (int/string), in order to track the type conversion
########################
sub handle_equation {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp($line);
	$line =~ s/\s+&//g;
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}

	# an equation only has two elements: variable, and value
	$line =~ s/^ +//;
	$line =~ s/ +$//;
	my @words = split /=/, $line;
	my $variable = $words[0];
	my $value = $words[1];
	$variable =~ s/^ +//;
	$variable =~ s/ +$//;
	$value =~ s/^ +//;

	# if value is a pure string (in single quotes)
	if ($value =~ /^\'.*\'$/) {
		print "$variable = $value";
	}
	elsif ($value =~ /^\".*\"$/) {
		$value =~ s/^\"//;
		$value =~ s/\"$//;
		$value = handle_expr($value, 0, 0, 0, 0);
		print "$variable = \"$value\"";
	}

	# if value contains variable
	elsif ($value =~ /.+ *.*\$.* *.*/) {

		# and if value is an arithmetic expre, like 5 * $number
		if ($value =~ /\+|\-|\*|\/|\%/) {
			$value = handle_variable($value, 0, 0, 0, 0);
			print "$variable = $value";
			$variable_type{$variable} = "int";
		}
		else {
			$value = handle_variable($value, 0, 0, 0, 0);
			print "$variable = $value";
			$variable_type{$variable} = "string";
		}
	}

	# if value is a number
	elsif ($value =~ /^[0-9]+$|^\-[0-9]+$/ && $value !~ /\$/) {
		$variable_type{$variable} = "int";
		print "$variable = $value";
	}

	# if value is an expression, like $(xxxx)
	elsif ($value =~ /^\$\(.+\)$/) {
		$value = handle_variable($value, 0, 0, 0, 0);
	}

	# if value is a variable
	elsif ($value =~ /^\$/) {

		# and if value is a system variable
		if ($value =~ /^\$[0-9]+$/) {
			$value =~ s/^\$//;
			$variable_type{$variable} = "string";
			print "$variable = sys.argv[$value]";
		}

		# and if value is a normal variable
		else {
			$value =~ s/^\$//;
			if (exists($variable_type{$value})) {
				$variable_type{$variable} = $variable_type{$value};
			}
			print "$variable = $value";
		}
	}

	# if not a variable
	else {
		$variable_type{$variable} = "string";
		print "$variable = \'$value\'";
	}
	if (!$isif && !$iscomment && !$iswhile) {
		print "\n";
	}
}

######################## level 0
# handle_cd
########################
sub handle_cd {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp($line);
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}

	my @words = split / /, $line;
	print "os.chdir(\'";
	print "$words[1]";
	print "\')";
	if (!$isif && !$iscomment && !$iswhile) {
		print "\n";
	}
}

###################################################################
#								  #
# 			  level 1 functions 			  #
#								  #
###################################################################

######################## level 1
# handle_for_loop
# including handle nested for/while loops and if condition
########################
sub handle_for_loop {
	my ($stack, $tabs, $isif, $iscomment, $iswhile) = @_;
	my @for_stack = @$stack;
	@for_loop_stack = ();
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}

	# store the variable name and values in for loop
	# handle the first line of for loop
	$for_stack[0] =~ s/^ +//;
	$for_stack[0] =~ s/ +/ /;
	my $left;
	my $right;
	my @words;

	# if the loop contains comments, e.g., for n in xxx # xxx is test
	if ($for_stack[0] =~ /.+[^\$]#.+/) {
		$iscomment = 1;
		my @sublines = split(/#/, $for_stack[0]);
		chomp(@sublines);
		$left = $sublines[0];
		$right = $sublines[1];
		$left =~ s/ +$//;
	}
	if ($iscomment) {
		@words = split / /, $left;
	}
	else {
		@words = split / /, $for_stack[0];
	}

	# handle the first line, e.g., for n in xxx (with or withou comments)
	# @value is the variable and range of for loop
	my $variable = $words[1];
	print "for $variable in ";
	my @values = ();
	foreach my $value (@words[3 .. $#words]) {
		push @values, $value;
	}

	# if the loop is c like
	if ($values[0] =~ /\{.+\}/) {
		$values[0] =~ s/ +//g;
		$values[0] =~ s/\{/range(/;
		$values[0] =~ s/\.\./, /;
		$values[0] =~ s/\}/\)/;
		print "$values[0]";
		if ($iscomment) {
			$right =~ s/ +$//;
			print ": #$right\n";
			$iscomment = 0;
		}
		else {
			print ":\n";
		}
	}

	# if the loop range is in a file
	elsif ($values[0] =~ /\*\.[A-Za-z]+/) {
		print "sorted(glob.glob(\"$values[0]\"))";
		if ($iscomment) {
			$right =~ s/ +$//;
			print ": #$right\n";
			$iscomment = 0;
		}
		else {
			print ":\n";
		}
	}
	else {

		# if the first loop range is a string
		if ($values[0] !~ /^[0-9]+$|^\-[0-9]+$/) {
			print "\'$values[0]\'";
		}

		# if the first loop range is a number
		else {
			print "$values[0]";
		}

		# handle the rest of the loop range
		foreach my $value (@values[1 .. $#values]) {
			print ", ";
			if ($value !~ /^[0-9]+$|^\-[0-9]+$/) {
				print "\'$value\'";
			}
			else {
				print "$value";
			}
		}
		if ($iscomment) {
			$right =~ s/ +$//;
			print ": #$right\n";
			$iscomment = 0;
		}
		else {
			print ":\n";
		}
	}

	# handle the rest of the lines in the for stack, start from "do"
	my @loop_stack = ();
	my @if_c_stack = ();
	my $bound_loop = 0;
	my $bound_if = 0;
	my $while_loop = 0;
	my $if_loop = 0;
	my $tab_level = 0;
	foreach my $line (@for_stack[1 .. $#for_stack]) {

		# a nested for/while loop, or if condition detected
		if ($line =~ /\bwhile\b|\bfor\b|\bif\b|\belif\b|\belse\b/ || $bound_loop == 1 || $bound_if == 1) {
			if (!$bound_loop && !$bound_if) {		
				$tab_level = count_leading_spaces($line);
			}

			# it is a nested loop
			if (($line =~ /\bwhile\b|\bfor\b/ || $bound_loop == 1) && $bound_if == 0) {
				if ($line =~ /\bwhile\b/ && !$bound_loop) {
					$while_loop = 1;
				}
				elsif ($line =~ /\bfor\b/ && !$bound_loop) {
					$for_loop = 1;
				}
				$bound_loop = 1;
				push @loop_stack, $line;

				# check the tabs, to determine whether is the end of the loop
				# e.g.:
				# while xxx: (tabs = 0)
				# do
				#     while yyy: (tabs = 4)
				#     do
				#         ...
				#         ...
				#     done (tabs = 4, matches to the nested while)
				# done (tabs = 0, matches to the main while)
				if ($line =~ /\bdone\b/) {

					# if same, then nested loop ends here
					if ($tab_level == count_leading_spaces($line)) {
						$bound_loop = 0;
						if ($while_loop) {
							handle_while_loop(\@loop_stack, $tab_level, 0, 0, 0);
							@loop_stack = ();
						}
						elsif ($for_loop) {
							handle_for_loop(\@loop_stack, $tab_level, 0, 0, 0);
							@loop_stack = ();
						}
					}
				}
			}

			# it is a nested if condition
			elsif (($line =~ /\bif\b|\belif\b|\belse\b/ || $bound_if == 1) && $bound_loop == 0) {
				if ($line !~ /\bfi\b/) {
					$bound_if = 1;
					push @if_c_stack, $line;
					my $current_index = get_index($line, @for_stack);
					if ($for_stack[$current_index + 1] =~ /\belif\b|\belse\b/) {
						handle_if_condition(\@if_c_stack, $tab_level, 0, 0, 0);
						@if_c_stack = ();
					}
				}
				# check the tabs, to determine whether is the end of the if condition
				elsif ($line =~ /\bfi\b/) {
					push @if_c_stack, $line;
					# if same, then nested if condition ends here
					if ($tab_level == count_leading_spaces($line)) {
						$bound_if = 0;
						handle_if_condition(\@if_c_stack, $tab_level, 0, 0, 0);
						@if_c_stack = ();
					}
				}
			}
		}

		# if there is no nested thing, handle the line
		elsif (!$bound_loop && !$bound_if) {
			$tabs = count_leading_spaces($line);
			chomp($line);
			$line =~ s/^\s*//;

			# handle pure comment lines in for loop
			if ($line =~ /^ *#.+/) {
				for (my $i = 0; $i < $tabs; $i ++) {
					print " ";
				}
				print "$line\n";
			}

			else {
				if ($line =~ /\bdone\b|\bdo\b/ && $line =~ /\#/) {
					check_line($line, $tabs, 0, $iscomment, 0);
				}
				elsif ($line =~ /\bdone\b|\bdo\b/ && $line !~ /\#/) {
					next;
				}
				else {
					check_line($line, $tabs, 0, $iscomment, 0);
				}
			}
		}
	}
}

######################## level 1
# handle_exit
########################
sub handle_exit {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp($line);
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}

	my @words = split / /, $line;
	print "sys.exit(";
	print "$words[1]";
	print ")";
	if (!$isif && !$iscomment && !$iswhile) {
		print "\n";
	}
}

######################## level 1
# handle_read
########################
sub handle_read {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp($line);
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}

	my @words = split / /, $line;
	print "$words[1]";
	print " = sys.stdin.readline().rstrip()";
	if (!$isif && !$iscomment && !$iswhile) {
		print "\n";
	}
}

###################################################################
#								  #
# 			  level 2 functions 			  #
#								  #
###################################################################

######################## level 2
# handle_if_condition
# including handle nested for/while loops and if condition
########################
sub handle_if_condition {
	my ($stack, $tabs, $isif, $iscomment, $iswhile) = @_;
	my @if_stack = @$stack;
	@if_condition_stack = ();
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}

	# handle the first line, like "if test this_assignment = damn" or "elif test this_assignment = samn"
	$if_stack[0] =~ s/^ +//;
	$if_stack[0] =~ s/ +/ /;
	my $left;
	my $right;
	my @words;
	my @syntax_first_line = ();

	# handle if conditions containing comments, same principle as it in while/for
	if ($if_stack[0] =~ /.+[^\$]#.+/) {
		$iscomment = 1;
		my @sublines = split(/#/, $if_stack[0]);
		chomp(@sublines);
		$left = $sublines[0];
		$right = $sublines[1];
		$left =~ s/ +$//;
	}
	if ($iscomment) {
		@words = split / /, $left;
	}
	else {
		@words = split / /, $if_stack[0];
	}

	# handle the first line, e.g., if test this_assignment = damn (with or withou comments)
	foreach my $word (@words[1 .. $#words]) {
		push @syntax_first_line, $word;
	}
	my $syntax_string = join(" ", @syntax_first_line);
	if ($words[0] =~ /\bif\b|\belif\b|\belse\b/) {

		# if first line is if or elif, which means it includes syntax
		if ($words[0] =~ /\bif\b|\belif\b/) {
			if ($words[0] =~ /\bif\b/) {
				print "if ";
			}
			elsif ($words[0] =~ /\belif\b/) {
				print "elif ";
			}

			# if brackets in syntax string
			if ($syntax_string =~ /\[|\]/) {
				handle_bracket($syntax_string, 0, 1, 0, $iswhile);
			}
			else {
				check_line($syntax_string, 0, 1, 0, $iswhile);
			}
		}

		# if first line is else, which means no syntax
		elsif ($words[0] =~ /\belse\b/) {
			print "else";
		}
		if ($iscomment) {
			$right =~ s/ +$//;
			print ": #$right\n";
			$iscomment = 0;
		}
		else {
			print ":\n";
		}
	}

	# handle the rest of the lines in the if stack, start from "then"
	my @loop_stack = ();
	my @if_c_stack = ();
	my $bound_loop = 0;
	my $bound_if = 0;
	my $while_loop = 0;
	my $if_loop = 0;
	my $tab_level = 0;
	foreach my $line (@if_stack[1 .. $#if_stack]) {

		# a nested for/while loop, or if condition detected
		if ($line =~ /\bwhile\b|\bfor\b|\bif\b|\belif\b|\belse\b/ || $bound_loop == 1 || $bound_if == 1) {
			if (!$bound_loop && !$bound_if) {		
				$tab_level = count_leading_spaces($line);
			}

			# is a nested loop
			if (($line =~ /\bwhile\b|\bfor\b/ || $bound_loop == 1) && $bound_if == 0) {
				if ($line =~ /\bwhile\b/ && !$bound_loop) {
					$while_loop = 1;
				}
				elsif ($line =~ /\bfor\b/ && !$bound_loop) {
					$for_loop = 1;
				}
				$bound_loop = 1;
				push @loop_stack, $line;

				# check the tabs, to determine whether is the end of the loop
				# if same, then nested loop ends here
				if ($line =~ /\bdone\b/) {
					if ($tab_level == count_leading_spaces($line)) {
						$bound_loop = 0;
						if ($while_loop) {
							handle_while_loop(\@loop_stack, $tab_level, 0, 0, 0);
							@loop_stack = ();
						}
						elsif ($for_loop) {
							handle_for_loop(\@loop_stack, $tab_level, 0, 0, 0);
							@loop_stack = ();
						}
					}
				}
			}

			# it is a nested if condition
			elsif (($line =~ /\bif\b|\belif\b|\belse\b/ || $bound_if == 1) && $bound_loop == 0) {
				if ($line !~ /\bfi\b/) {
					$bound_if = 1;
					push @if_c_stack, $line;
					my $current_index = get_index($line, @if_stack);
					if ($if_stack[$current_index + 1] =~ /\belif\b|\belse\b/) {
						handle_if_condition(\@if_c_stack, $tab_level, 0, 0, 0);
						@if_c_stack = ();
					}
				}
				# check the tabs, to determine whether is the end of the if condition
				elsif ($line =~ /\bfi\b/) {
					push @if_c_stack, $line;
					# if same, then nested if condition ends here
					if ($tab_level == count_leading_spaces($line)) {
						$bound_if = 0;
						handle_if_condition(\@if_c_stack, $tab_level, 0, 0, 0);
						@if_c_stack = ();
					}
				}
			}
		}

		# if there is no nested thing, handle the line
		elsif (!$bound_loop && !$bound_if) {
			$tabs = count_leading_spaces($line);
			chomp($line);
			$line =~ s/^ *//;
			$line =~ s/ *$//;

			# handle pure comment lines in if conditions
			if ($line =~ /^ *#.+/) {
				for (my $i = 0; $i < $tabs; $i ++) {
					print " ";
				}
				print "$line\n";
			}
			
			else {
				if ($line =~ /\bfi\b|\bthen\b/ && $line =~ /\#/) {
					check_line($line, $tabs, 0, $iscomment, 0);
				}
				elsif ($line =~ /\bfi\b|\bthen\b/ && $line !~ /\#/) {
					next;
				}
				else {
					check_line($line, $tabs, 0, $iscomment, 0);
				}
			}
		}
	}
}

######################## level 2 / level 3
# handle_test
# this subroutine will handle the syntax with command test, including:
# syntax with -o / -a in if condition
# equations with variables and values
# test command with options
# test command with comparison
########################
sub handle_test {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp($line);
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}

	my @words = split / /, $line;

	# in if condition, "-o" is or, "-a" is and, e.g., if test xxxxx -a xxxxx
	if ($line =~ /\-o|\-a/) {
		my $or_and_index = 0;
		my $connector;
		my @syntax_left = ();
		my @syntax_right = ();

		# identify the position of "-a" or "-o", and split the syntax according to this index
		if ($line =~ /\-o/) {
			$connector = "or";
			$or_and_index = get_index("-o", @words);
		}
		elsif ($line =~ /\-a/) {
			$connector = "and";
			$or_and_index = get_index("-a", @words);
		}
		foreach my $word (@words[1 .. $or_and_index - 1]) {
			push @syntax_left, $word;
		}
		foreach my $word (@words[$or_and_index + 1 .. $#words]) {
			push @syntax_right, $word;
		}
		my $syntax_left_result = join(" ", @syntax_left);
		my $syntax_right_result = join(" ", @syntax_right);
		chomp($syntax_left_result);
		chomp($syntax_right_result);
		$syntax_left_result =~ s/^ +//;
		$syntax_left_result =~ s/ +$//;
		$syntax_right_result =~ s/^ +//;
		$syntax_right_result =~ s/ +$//;
		check_line($syntax_left_result, 0, 1, $iscomment, 0);
		if ($connector eq "or") {
			print " or ";
		}
		elsif ($connector eq "and") {
			print " and ";
		}
		check_line($syntax_right_result, 0, 1, $iscomment, 0);
	}

	# it is a variable and a value, e.g., test xxx = yyy
	elsif ($line =~ /\=/) {
		my $variable = $words[1];
		my $value = $words[3];

		# variable is a true variable
		if ($variable =~ /\$/) {
			$variable =~ s/\$//g;
			if ($variable =~ /[0-9]+/) {
				if ($value =~ /[0-9]+/) {
					print "sys.argv[$variable] == $value";
				}
				else {
					print "sys.argv[$variable] == \'$value\'";
				}
			}
			else {
				if ($value =~ /^[0-9]+$|^\-[0-9]+$/) {
					print "$variable == $value";
				}
				else {
					print "$variable == \'$value\'";
				}
			}
		}

		# variable is a string or number, not a true variable
		else {
			if ($variable =~ /^[0-9]+$|^\-[0-9]+$/) {
				if ($value =~ /^[0-9]+$|^\-[0-9]+$/) {
					print "$variable == $value";
				}
				else {
					print "$variable == \'$value\'";
				}
			}
			else {
				if ($value =~ /^[0-9]+$|^\-[0-9]+$/) {
					print "\'$variable\' == $value";
				}
				else {
					print "\'$variable\' == \'$value\'";
				}
			}
		}
	}

	# if it is a test command with options, e.g., test -r <command>
	elsif ($line =~ /\-[a-z]{1} {1}/) {
		my $file = $words[2];

		# the syntax tries to reach a file/directory
		if ($line =~ /\-r/) {
			if ($file =~ /^\$/) {
				$file =~ s/^\$//;
				print "os.access($file, os.R_OK)";
			}
			else {
				print "os.access(\'$file\', os.R_OK)";
			}
		}

		# the syntax tries to detect whether is a directory / whether is a file / whether the file exists
		elsif ($line =~ /\-d/) {
			print "os.path.isdir(\'$file\')";
		}
		elsif ($line =~ /\-f/) {
			print "os.path.isfile(\'$file\')";
		}
		elsif ($line =~ /\-a/) {
			print "os.path.exists(\'$file\')";
		}
	}

	# if it is a comparison, e.g., test xx -eq yy
	elsif ($line =~ /\-eq|\-le|\-lt|\-ge|\-gt|\-ne|==|<=|>=|<|>/) {
		my @syntax = ();
		my $compare = $words[2];
		my $left = $words[1];
		my $right = $words[3];
		$left = handle_variable($left, 0, 0);
		$right = handle_variable($right, 0, 0);
		push @syntax, $left;
		push @syntax, $compare;
		push @syntax, $right;
		my $comparison_syntax = join(" ", @syntax);
		handle_comparison($comparison_syntax, $tabs, $isif, $iscomment, $iswhile);
	}
	if (!$isif && !$iscomment && !$iswhile) {
		print "\n";
	}
}

###################################################################
#								  #
# 			  level 3 functions 			  #
#								  #
###################################################################

######################## level 3
# handle_variable, not only for variables in fouble quotes
# this subroutine will handle all variables in shell script
# all the other subroutines will pass variables or a combination of variables to handle_variable
# and then handle_variable will return the processed result back to upper subroutines
########################
sub handle_variable {
	my ($word, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp($word);
	$word =~ s/^ +//;
	$word =~ s/ +$//;

	# if the variable has no back quots and no $(xxx)
	if ($word =~ /\$/ && $word !~ /\`.+\`/ && $word !~ /^\$\(.+\)$/) {
		$word =~ s/^\$//;

		# a system variable
		if ($word =~ /\@/) {
			return "sys.argv[1:]";
		}
		elsif ($word =~ /\#/) {
			return "len(sys.argv[1:])";
		}
		elsif ($word =~ /\*/) {
			return "sys.argv[1:]";
		}
		elsif ($word =~ /^[0-9]+/) {
			$word =~ s/\"//g;
			return "sys.argv[$word]";
		}

		# variable is a syntax's result
		elsif ($word =~ /^\(.+\)/) {
			$word =~ s/^\(//;
			$word =~ s/\)$//;
			my $expr = handle_expr($word, 0, 0, 0, 0);
			return $expr;
		}

		# a named variable
		else {
			$word =~ s/\"//g;
			$word =~ s/\$//g;
			return $word;
		}
	}

	# if the variable has back quotes or $(xxx), e.g., $(xxx + $yyy)
	elsif ($word =~ /\`.+\`|^\$\(.+\)$/) {
		$word =~ s/\`//g;
		if ($word =~ /^\$\(.+\)$/) {
			$word =~ s/^\$\(//;
			$word =~ s/\)$//;
		}
		if ($word =~ /expr|\$/) {
			$word = handle_expr($word);
			return $word;
		}
		else {
			return "\'$word\'";
		}
	}

	# if the variable is not a true variale, just return the original word, e.g.:
	# "xxx
	# yyy
	# zzz"
	else {
		return $word;
	}
}

######################## level 3
# handle_while_loop
# including handle nested for/while loops and if condition
########################
sub handle_while_loop {
	my ($stack, $tabs, $isif, $iscomment, $inwhile) = @_;
	my @while_stack = @$stack;
	@while_loop_stack = ();
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}

	$while_stack[0] =~ s/^ +//;
	$while_stack[0] =~ s/ +/ /;
	my $left;
	my $right;
	my @words;

	# if the loop contains comments, e.g., while xxx # xxx is test
	if ($while_stack[0] =~ /.+[^\$]#.+/) {
		$iscomment = 1;
		my @sublines = split(/#/, $while_stack[0]);
		chomp(@sublines);
		$left = $sublines[0];
		$right = $sublines[1];
		$left =~ s/ +$//;
	}
	if ($iscomment) {
		@words = split / /, $left;
	}
	else {
		@words = split / /, $while_stack[0];
	}

	# handle the first line, e.g., while xxx (with or without comments)
	my @syntax_first_line = ();
	foreach my $word (@words[1 .. $#words]) {
		push @syntax_first_line, $word;
	}
	my $syntax_string = join(" ", @syntax_first_line);
	print "while ";
	my $iswhile = 1;

	# if the syntax contains brackets
	if ($syntax_string =~ /\[|\]/) {
		handle_bracket($syntax_string, 0, $isif, $iscomment, $iswhile);
	}
	else {
		check_line($syntax_string, 0, $isif, $iscomment, $iswhile);
	}
	if ($iscomment) {
		$right =~ s/ +$//;
		print ": #$right\n";
		$iscomment = 0;
	}
	else {
		print ":\n";
	}

	# handle the rest of the lines in the while stack, start from "do"
	my @loop_stack = ();
	my @if_c_stack = ();
	my $bound_loop = 0;
	my $bound_if = 0;
	my $while_loop = 0;
	my $if_loop = 0;
	my $tab_level = 0;
	foreach my $line (@while_stack[1 .. $#while_stack]) {

		# a nested for/while loop, or if condition detected
		if ($line =~ /\bwhile\b|\bfor\b|\bif\b|\belif\b|\belse\b/ || $bound_loop == 1 || $bound_if == 1) {
			if (!$bound_loop && !$bound_if) {		
				$tab_level = count_leading_spaces($line);
			}
			if (($line =~ /\bwhile\b|\bfor\b/ || $bound_loop == 1) && $bound_if == 0) {
				if ($line =~ /\bwhile\b/ && !$bound_loop) {
					$while_loop = 1;
				}
				elsif ($line =~ /\bfor\b/ && !$bound_loop) {
					$for_loop = 1;
				}
				$bound_loop = 1;
				push @loop_stack, $line;

				# check the tabs, to determine whether is the end of the loop
				if ($line =~ /\bdone\b/) {

					# if same, then nested loop ends here
					if ($tab_level == count_leading_spaces($line)) {
						$bound_loop = 0;
						if ($while_loop) {
							handle_while_loop(\@loop_stack, $tab_level, 0, 0, 0);
							@loop_stack = ();
						}
						elsif ($for_loop) {
							handle_for_loop(\@loop_stack, $tab_level,0 , 0, 0);
							@loop_stack = ();
						}
					}
				}
			}

			# it is a nested if condition
			elsif (($line =~ /\bif\b|\belif\b|\belse\b/ || $bound_if == 1) && $bound_loop == 0) {
				if ($line !~ /\bfi\b/) {
					$bound_if = 1;
					push @if_c_stack, $line;
					my $current_index = get_index($line, @while_stack);
					if ($while_stack[$current_index + 1] =~ /\belif\b|\belse\b/) {
						handle_if_condition(\@if_c_stack, $tab_level, 0, 0, 0);
						@if_c_stack = ();
					}
				}
				# check the tabs, to determine whether is the end of the if condition
				elsif ($line =~ /\bfi\b/) {
					push @if_c_stack, $line;
					# if same, then nested if condition ends here
					if ($tab_level == count_leading_spaces($line)) {
						$bound_if = 0;
						handle_if_condition(\@if_c_stack, $tab_level, 0, 0, 0);
						@if_c_stack = ();
					}
				}
			}
		}

		# if there is no nested thing, handle the line
		elsif (!$bound_loop && !$bound_if) {
			$tabs = count_leading_spaces($line);
			chomp($line);
			$line =~ s/^\s*//;

			# handle pure comment lines in while loop
			if ($line =~ /^ *#.+/) {
				for (my $i = 0; $i < $tabs; $i ++) {
					print " ";
				}
				print "$line\n";
			}
			
			else {
				if ($line =~ /\bdone\b|\bdo\b/ && $line =~ /\#/) {
					check_line($line, $tabs, 0, $iscomment, 0);
				}
				elsif ($line =~ /\bdone\b|\bdo\b/ && $line !~ /\#/) {
					next;
				}
				else {
					check_line($line, $tabs, 0, $iscomment, 0);
				}
			}
		}
	}
}

######################## level 3
# handle_comparison
# this subroutine will handle comparisons like -le, -eq, etc.
# and add type conversion
########################
sub handle_comparison {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp($line);
	$line =~ s/^ +//;
	$line =~ s/ +$//;
	my @words = split / /, $line;
	my $compare = $words[1];
	my $left = $words[0];
	my $right = $words[2];
	$left = handle_variable($left, 0, 0);
	$right = handle_variable($right, 0, 0);

	# if the type is not int then add force type conversion
	if ($left !~ /^[0-9]+$|^\-[0-9]+$/ && $left !~ /len\(.+\)/) {
		if ($variable_type{$left} ne "int") {
			$left = "int($left)";
		}
	}
	if ($right !~ /^[0-9]+$|^\-[0-9]+$/ && $right !~ /len\(.+\)/) {
		if ($variable_type{$right} ne "int") {
			$right = "int($right)";
		}
	}
	if ($compare =~ /\-eq|==|'=='|"=="/) {
		print "$left == $right";
	}
	elsif ($compare =~ /\-le|<=|'<='|"<="/) {
		print "$left <= $right";
	}
	elsif ($compare =~ /\-lt|<|'<'|"<"/) {
		print "$left < $right";
	}
	elsif ($compare =~ /\-ge|>=|'>='|">="/) {
		print "$left >= $right";
	}
	elsif ($compare =~ /\-gt|>|'>'|">"/) {
		print "$left > $right";
	}
	elsif ($compare =~ /\-ne|!=|'!='|"!="/) {
		print "$left != $right";
	}
}

######################## level 3
# handle_expr
# other subroutines will pass variables to here if it detects that the syntax
# contains command expr, or the syntax is a result of an expression, e.g., $(xxx + $yyy)
# then handle_expr will return the result of processed syntax in python
########################
sub handle_expr {
	my ($syntax, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp($syntax);

	$syntax =~ s/^\(//;
	$syntax =~ s/\)$//;
	@words = split(/ /, $syntax);
	my @result = ();
	my $index = 0;
	if ($syntax =~ /expr/) {
		$index = 1;
	}

	# split the syntax and loop in every word
	foreach my $word (@words[$index .. $#words]) {

		# if it is a variable
		if ($word =~ /\$/) {
			$word =~ s/^\$//;

			# a system variables
			if ($word =~ /\@/) {
				push @result, "sys.argv[1:]";
			}
			elsif ($word =~ /^[0-9]+/) {
				$word =~ s/\"//g;
				push @result, "sys.argv[$word]";
			}

			# a normal variable
			else {
				$word =~ s/\"//g;
				if (exists($variable_type{$word})) {
					if ($variable_type{$word} eq "int") {
						push @result, "$word";
					}
					else {
						push @result, "int($word)";
					}
				}
				else {
					push @result, "int($word)";
				}
			}
		}

		# if it is not a variable, and it is a number
		elsif ($word =~ /[0-9]+|\-[0-9]+$/ && $word !~ /\$/ && $word !~ /[a-zA-Z]/) {
			push @result, $word;
		}

		# if it is not a variable, and it is a symbol
		elsif ($word =~ /\*|\+|\%|\-|\//) {
			$word =~ s/\'//g;
			$word =~ s/\"//g;
			push @result, $word;
		}

		# if it is not a variable, and it is a string
		elsif ($word !~ /\*|\+|\%|\-|\/| /) {
			$word =~ s/\'//g;
			$word =~ s/\"//g;
			push @result, $word;
		}
	}
	my $result_string = join(" ", @result);
	return $result_string;
}

###################################################################
#								  #
# 			  level 4 functions 			  #
#								  #
###################################################################

######################## level 4
# handle_bracket
########################
sub handle_bracket {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp($line);
	$line =~ s/\[//g;
	$line =~ s/\]//g;
	$line =~ s/^ +//g;
	$line =~ s/ +$//g;
	if ($line =~ /\-eq|\-le|\-lt|\-ge|\-gt|\-ne|==|<=|>=|<|>/ ) {
		handle_comparison($line, $tabs, $isif, $iscomment, $iswhile);
	}

	# the $line is with options
	elsif ($line =~ /\-[a-z]{1} {1}/) {
		my @words = split(/ /, $line);
		my $file = $words[1];

		if ($file =~ /^\$/) {
			$file =~ s/^\$//;
			# try to reach a file/directory
			if ($line =~ /\-r/) {
				print "os.access(str($file), os.R_OK)";
			}

			# the syntax tries to detect whether is a directory / whether is a file / whether the file exists
			elsif ($line =~ /\-d/) {
				print "os.path.isdir(str($file))";
			}
			elsif ($line =~ /\-f/) {
				print "os.path.isfile(str($file))";
			}
			elsif ($line =~ /\-a/) {
				print "os.path.exists(str($file))";
			}
		}

		else {
			# try to reach a file/directory
			if ($line =~ /\-r/) {
				print "os.access(\'$file\', os.R_OK)";
			}

			# the syntax tries to detect whether is a directory / whether is a file / whether the file exists
			elsif ($line =~ /\-d/) {
				print "os.path.isdir(\'$file\')";
			}
			elsif ($line =~ /\-f/) {
				print "os.path.isfile(\'$file\')";
			}
			elsif ($line =~ /\-a/) {
				print "os.path.exists(\'$file\')";
			}
		}
	}
	if (!$isif && !$iscomment && !$iswhile) {
		print "\n";
	}
}

######################## level 4
# handle_fgrep
########################
sub handle_fgrep {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp($line);
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}

	my @words = split / /, $line;
	print "not subprocess.call([";
	if ($words[0] =~ /^\$/) {
		$words[0] =~ s/\$//;
		print "str($words[0])";
		$variable_type{$words[0]} = "string";
	}
	else {
		print "\'$words[0]\'";
	}
	foreach $word (@words[1 .. $#words]) {
		if ($word =~ /^\$/) {
			$word =~ s/\$//;
			print ", str($word)";
			$variable_type{$word} = "string";
		}
		else {
			print ", \'$word\'";
		}
	}
	print "])";
	if (!$isif && !$iscomment && !$iswhile) {
		print "\n";
	}
}

######################## level 4
# handle_chmod
# python considers the privilege in os.chmod is decimal, and will convert it to an
# octal number, e.g., os.chmod(xxx, 436) (in decimal) actually works as os.chmod(xxx, 664) (in octal)
# and there is another way, put a 0 (python 2) or 0o (python 3) before the number, to notify python
# that the number inputed is an octal number, e.g., os.chmod(xxx, 0436) (add a 0) works as os.chmod(xxx, 436) (in octal)
########################
sub handle_chmod {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp($line);
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}

	my @words = split / /, $line;
	print "os.chmod(";
	my $privilege = $words[1];
	my $file = $words[2];
	$privilege =~ s/^ +//;
	$privilege =~ s/ +$//;
	$file =~ s/^ +//;
	$file =~ s/ +$//;

	# if privilege is a number, e.g., 664
	if ($privilege =~ /[0-9]+/) {

		# file is a variable
		if ($file =~ /^\$/) {
			$file =~ s/^\$//;
			print "str($file), 0$privilege)";
		}

		# file is a string
		else {
			print "$file, 0$privilege)";
		}
	}

	# if privilege is an expression, e.g.:
	# -rw-rw-r--
	elsif ($privilege =~ /[\-rwxd]{7}/) {
		$privilege =~ s/^.{1}//;
		my @array = ($privilege =~ m/.../g);
		my $user_privilege = $table_privilege{$array[0]};
		my $group_privilege = $table_privilege{$array[1]};
		my $other_privilege = $table_privilege{$array[2]};
		
		# file is a variable
		if ($file =~ /^\$/) {
			$file =~ s/^\$//;
			print "str($file), 0$user_privilege$group_privilege$other_privilege)";
		}

		# file is a string
		else {
			print "$file, 0$user_privilege$group_privilege$other_privilege)";
		}
	}

	if (!$isif && !$iscomment && !$iswhile) {
		print "\n";
	}
}

######################## level 4
# handle_case_esac
# the switch/case is not provided in Python doc, hence I use dictionary to handle this
########################
sub handle_case_esac {
	my ($stack, $tabs, $isif, $iscomment, $inwhile) = @_;
	my @case_stack = @$stack;
	@case_esac_stack = ();
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}

	$case_counter ++;
	$case_stack[0] =~ s/^ +//;
	$case_stack[0] =~ s/ +/ /;
	my $left;
	my $right;
	my @words;

	# if the case contains comments, e.g., case xxx in # is test
	if ($case_stack[0] =~ /.+[^\$]#.+/) {
		$iscomment = 1;
		my @sublines = split(/#/, $case_stack[0]);
		chomp(@sublines);
		$left = $sublines[0];
		$right = $sublines[1];
		$left =~ s/ +$//;
	}
	if ($iscomment) {
		@words = split / /, $left;
	}
	else {
		@words = split / /, $case_stack[0];
	}

	##############################
	# handle the rest of the lines in the case stack
	# xxxx ) 
	#	<action1>
	#	<action2>
	# 	;;
	# yyyy ) 
	#	<action3>
	#	<action4>
	# 	;;
	# esac
	##############################
	# will be convert to:
	# def XX():
	#	<action1>
	#	<action2>
	#
	# def YY():
	#	<action3>
	#	<action4>
	#
	# case_esac = {
	#	xxxx : XXXX,
	#	yyyy : YYYY,
	# }
	#
	# and run in Python as:
	# case_esac[key]()
	##############################
	#
	# <case_choice> is a dictionary, called "case_esac" in Python, stores the <key_n:function_name>
	# <case_function> stores the functions in Python
	
	@case_function = ();
	@case_choice = ();
	@case_keylist = ();
	my $key = $words[1];

	# if key is a pure string (in single quotes), then do nothing
	# if key is a pure string (in double quotes), then do nothing
	# if key is a variable in double quotes, process it
	if ($key =~ /^\".*\"$/) {
		$key = handle_variable($key, 0, 0, 0, 0);
	}
	elsif ($key =~ /\$/) {
		$key =~ s/\$//;
	}

	# begin construct the dictionary <case_choice>
	push @case_choice, "case_esac${case_counter} = {";
	my $in_case = 0;
	foreach my $line (@case_stack[1 .. $#case_stack]) {
		chomp($line);
		$line =~ s/^ +//;
		$line =~ s/ +$//;

		# handle pure comment lines in case ... esac
		if ($line =~ /^ *#.+/) {
			for (my $i = 0; $i < $tabs; $i ++) {
				print " ";
			}
			print "$line\n";
		}

		else {
			my $value;
			my $f_name;

			# handle "actions" in cases, e.g., echo xxxxx
			# in the following parts, the STDOUT will be redirected to variable, rather than display on screen
			# and then push the variable (with the redirected output content) to <case_function>

			# if case and action are on the same line, e.g.:
			# xxxx ) <action> ;;
			#
			if ($line =~ /^ *.+\).+\;\; *$/) {
				my @sublines = split(/\)/, $line);
				chomp(@sublines);
				$value = $sublines[0];
				my $action = $sublines[1];
				$value =~ s/ +$//;
				$action =~ s/\;\;//;
				$action =~ s/ +$//;
				$action =~ s/^ +//;
				if ($value =~ /^[0-9]+$/) {
					$function_counter ++;
					$f_name = "FUNCTION$function_counter";
				}
				elsif ($value !~ /^\*$/) {
					$f_name = uc $value;
					$f_name =~ s/^\"//;
					$f_name =~ s/^\'//;
					$f_name =~ s/\"$//;
					$f_name =~ s/\'$//;
				}
				else {
					$value = "default";
					$f_name = 'DEFAULT_CASE';
				}
				push @case_choice, "    ${value}:${f_name}";
				push @case_function, "def ${f_name} ():";
				push @case_keylist, $value;

				my $current_index = get_index($line, @case_stack);
				if ($case_stack[$current_index + 1] !~ /\besac\b/) {
					push @case_choice, ",";
				}

				# redirect the STDOUT to variable
				my $STDOUT_result = '';
				open RESULT, '>', \$STDOUT_result or die $!;
				select RESULT;
				check_line($action, 0, 0, 0, 0);
				select STDOUT;
				chomp($STDOUT_result);
				push @case_function, "    $STDOUT_result";
				push @case_function, "";
			}

			# if the lines are splitted, e.g.:
			# xxxx ) 
			#	<action1>
			#	<action2>
			# 	;;
			#
			else {
				# if the line is pure action line
				if ($in_case && $line !~ /^ *\;\; *$/ && $line !~ /\besac\b/) {

					# redirect the STDOUT to variable
					my $STDOUT_result = '';
					open RESULT, '>', \$STDOUT_result or die $!;
					select RESULT;
					check_line($line, 0, 0, 0, 0);
					select STDOUT;
					chomp($STDOUT_result);
					push @case_function, "    $STDOUT_result";
				}

				# when comes to ";;"
				elsif ($line =~ /^ *\;\; *$/) {
					$in_case = 0;
					push @case_function, "";
					my $current_index = get_index($line, @case_stack);
					if ($case_stack[$current_index + 1] !~ /\besac\b/) {
						push @case_choice, ",";
					}
					next;
				}

				# when comes to a new case
				elsif ($line =~ /[^\(]+\)/) {
					$in_case = 1;
					my @sublines = split(/\)/, $line);
					chomp(@sublines);
					$value = $sublines[0];
					$value =~ s/ +$//;
					if ($value =~ /^[0-9]+$/) {
						$function_counter ++;
						$f_name = "FUNCTION$function_counter";
					}
					elsif ($value !~ /^\*$/) {
						$f_name = uc $value;
						$f_name =~ s/^\"//;
						$f_name =~ s/^\'//;
						$f_name =~ s/\"$//;
						$f_name =~ s/\'$//;
					}
					else {
						$value = "defualt";
						$f_name = 'DEFAULT_CASE';
					}
					push @case_choice, "    ${value}:${f_name}";
					push @case_function, "def ${f_name} ():";
					push @case_keylist, $value;
				}
			}
		}
		if ($line =~ /\besac\b/) {
			push @case_choice, "}";
			last;
		}
	}

	# display the case ... esac functions
	foreach my $function (@case_function) {
		print "$function\n";
	}

	foreach my $case (@case_choice[0 ... $#case_choice - 1]) {
		if ($case =~ /\,|\{|\}/) {
			print "$case\n";
		}
		else {
			print "$case";
		}
	}
	print "\n$case_choice[$#case_choice]\n";
	
	# this will run the case ... esac
	print "\ncase_esac${case_counter}[$key]()\n";
}

###################################################################
#								  #
# 			    sub loop 				  #
#								  #
###################################################################
# this is a very import subroutine, every other subroutine will call this to
# do "check line" to syntaxes, and this subroutine will also handle lines with comments, or an empty line
#
sub check_line {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp($line);
	my $in_for_loop = 0;
	my $in_while_loop = 0;
	my $in_if_condition = 0;

	if ($line =~ /^ *$/) {
		print "\n";
	}

	elsif ($line =~ /^#[^!]{1}.*/) {
		print "$line\n";
	}

	# handle pure comment lines
	elsif ($line =~ /^ *#.+/) {
		my $tab_level = count_leading_spaces($line);
		for (my $i = 0; $i < $tab_level; $i ++) {
			print " ";
		}
		$line =~ s/ +//;
		print "$line\n";
	}

	# handling comments in loop/if condition's useless lines, like do, done, fi
	elsif ($line =~ /^ *do *#.+|^ *done *#.+|^ *then *#.+|^ *fi *#.+/) {
		for (my $i = 0; $i < $tabs; $i ++) {
			print " ";
		}
		my @sublines = split(/#/, $line);
		chomp(@sublines);
		my $right = $sublines[1];
		$right =~ s/ +$//;
		print "#$right\n";
	}

	# use recursion to handle lines containing comments
	elsif ($line =~ /.+[^\$]#.+/) {
		my $iscomment = 1;
		my @sublines = split(/#/, $line);
		chomp(@sublines);
		my $left = $sublines[0];
		my $right = $sublines[1];
		$left =~ s/ +$//;
		check_line($left, $tabs, $isif, $iscomment, $iswhile);
		$right =~ s/ +$//;
		print " #$right\n";
	}

	######################## level 0
	# part of handling "echo"
	########################
	elsif ($line =~ /\becho\b/ && $line !~ /\".*echo.*\"/ && $line !~ /\'.*echo.*\'/ && $line !~ /echo=|=echo|\$echo/) {
		handle_echo($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 0
	# part of handling simple builtin commands and boolean, which needs subprocess in python
	########################
	elsif ($line =~ /$search_in_single_commands|\btrue\b|\bfalse\b/) {
		handle_simple_command($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 0
	# part of handling equations, line only contains variables
	########################
	elsif ((($line !~ /$search_in_single_commands/ 
		&& $line !~ /$search_in_translate_commands/ 
		&& $line !~ /$search_in_loop_key_words/ 
		&& $line !~ /$search_in_if_key_words/) || $line =~ /\`.+\`/ || $line =~ /\$\(.+\)/) 
		&& $line =~ /\=/) {
		handle_equation($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 1
	# part of handling "cd"
	########################
	elsif ($line =~ /\bcd\b/ && $line !~ /\".*cd.*\"/ && $line !~ /\'.*cd.*\'/ && $line !~ /cd=|=cd|\$cd/) {
		handle_cd($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 1
	# part of handling "exit"
	########################
	elsif ($line =~ /\bexit\b/ && $line !~ /\".*exit.*\"/ && $line !~ /\'.*exit.*\'/ && $line !~ /exit=|=exit|\$exit/) {
		handle_exit($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 1
	# part of handling "read"
	########################
	elsif ($line =~ /\bread\b/ && $line !~ /\".*read.*\"/ && $line !~ /\'.*read.*\'/ && $line !~ /read=|=read|\$read/) {
		handle_read($line, $tabs, $isif, $iscomment, $iswhile);
	}
	
	######################## level 2
	# part of handling "test"
	########################
	elsif ($line =~ /\btest\b/ && $line !~ /\".*test.*\"/ && $line !~ /\'.*test.*\'/ && $line !~ /test=|=test|\$test/) {
		handle_test($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 3
	# part of handling "comparison", this MUST be placed AFTER "handle_test"
	########################
	elsif ($line =~ /\-eq |\-le |\-lt |\-ge |\-gt |\-ne |==|<=|>=|<|>/) {
		handle_comparison($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 3
	# part of handling "expr"
	########################
	elsif ($line =~ /\bexpr\b/ && $line !~ /\`.+\`/ && $line !~ /\".*expr.*\"/ && $line !~ /\'.*expr.*\'/ && $line !~ /expr=|=expr|\$expr/) {
		handle_expr($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 4
	# part of handling "fgrep"
	########################
	elsif ($line =~ /\bfgrep\b|grep -F/ && $line !~ /\".*fgrep.*\"/ && $line !~ /\'.*fgrep.*\'/ && $line !~ /fgrep=|=fgrep|\$fgrep/) {
		handle_fgrep($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 4
	# part of handling "chmod"
	########################
	elsif ($line =~ /\bchmod\b/ && $line !~ /\".*chmod.*\"/ && $line !~ /\'.*chmod.*\'/ && $line !~ /chmod=|=chmod|\$chmod/) {
		handle_chmod($line, $tabs, $isif, $iscomment, $iswhile);
	}

	# Lines we can't translate are turned into comments
	else {
		print "#$line\n";
	}
}

###################################################################
#								  #
# 			    main loop 				  #
#								  #
###################################################################
# this is the main loop, the very first initial loop starts from here
# and the imported libraries will be defined in here
#
foreach my $line (@input_lines) {

	# part of program declaration
	if ($line =~ /^#!\// && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		print "#!/usr/bin/python2.7 -u\n";
		check_import_libraries();
	}

	elsif ($line =~ /^\s*$/ && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		print "\n";
	}

	elsif ($line =~ /^#[^!]{1}.*/ && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		print "$line\n";
	}

	# handle pure comment lines
	elsif ($line =~ /^ *#.+/
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		my $tab_level = count_leading_spaces($line);
		for (my $i = 0; $i < $tab_level; $i ++) {
			print " ";
		}
		$line =~ s/ +//;
		print "$line\n";
	}

	# part of handling comments in normal lines (not in for/while loop and if conditions)
	elsif ($line =~ /.+[^\$]#.+/ && $line !~ /\bif\b|\belif\b|\belse\b|\bfor\b|\bwhile\b/ 
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		my $iscomment = 1;
		my @sublines = split(/#/, $line);
		chomp(@sublines);
		my $left = $sublines[0];
		my $right = $sublines[1];
		$left =~ s/ +$//;
		check_line($left, 0, 0, $iscomment, 0);
		$right =~ s/ +$//;
		print " #$right\n";
	}
	
	######################## level 0
	# part of handling "echo"
	# part of handling "echo -n"
	# part of handling "echo" variables
	########################
	elsif ($line !~ /$search_in_loop_key_words/ && $line !~ /$search_in_if_key_words/ 
		&& $line =~ /\becho\b/ && $line !~ /\".*echo.*\"/ && $line !~ /\'.*echo.*\'/ && $line !~ /echo=|=echo|\$echo/
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		handle_echo($line, 0, 0, 0, 0);
	}

	######################## level 0
	# part of handling simple builtin commands, which needs subprocess in python
	########################
	elsif ($line !~ /$search_in_loop_key_words/ && $line !~ /$search_in_if_key_words/ 
		&& $line =~ /$search_in_single_commands/
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		handle_simple_command($line, 0, 0, 0, 0);
	}

	######################## level 0
	# part of handling equations, line only contains variables
	########################
	elsif ((($line !~ /$search_in_single_commands/ 
		&& $line !~ /$search_in_translate_commands/ 
		&& $line !~ /$search_in_loop_key_words/ 
		&& $line !~ /$search_in_if_key_words/) || $line =~ /\`.+\`/) 
		&& $line =~ /\=/ 
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		handle_equation($line, 0, 0, 0, 0);
	}

	######################## level 1
	# part of handling "cd"
	########################
	elsif ($line !~ /$search_in_loop_key_words/ && $line !~ /$search_in_if_key_words/ 
		&& $line =~ /\bcd\b/ && $line !~ /\".*cd.*\"/ && $line !~ /\'.*cd.*\'/ && $line !~ /cd=|=cd|\$cd/
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		handle_cd($line, 0, 0, 0, 0);
	}

	######################## level 1
	# part of handling "for" loop
	########################
	elsif (($line =~ /\bfor\b/ || $in_for_loop == 1) && $line !~ /\".*for.*\"/ && $line !~ /\'.*for.*\'/
		&& $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		$in_for_loop = 1;
		if ($line !~ /\bdone\b/) {
			push @for_loop_stack, $line;
			next;
		}
		elsif ($line =~ /\bdone\b/) {
			push @for_loop_stack, $line;
			if (count_leading_spaces($line) == 0) {
				$in_for_loop = 0;
			}
			else {
				next;
			}
		}
		handle_for_loop(\@for_loop_stack, 0, 0, 0, 0);
	}

	######################## level 1
	# part of handling "exit"
	########################
	elsif ($line !~ /$search_in_loop_key_words/ && $line !~ /$search_in_if_key_words/ 
		&& $line =~ /\bexit\b/ && $line !~ /\".*exit.*\"/ && $line !~ /\'.*exit.*\'/ && $line !~ /exit=|=exit|\$exit/
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		handle_exit($line, 0, 0, 0, 0);
	}

	######################## level 1
	# part of handling "read"
	########################
	elsif ($line !~ /$search_in_loop_key_words/ && $line !~ /$search_in_if_key_words/ 
		&& $line =~ /\bread\b/ && $line !~ /\".*read.*\"/ && $line !~ /\'.*read.*\'/ && $line !~ /read=|=read|\$read/
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		handle_read($line, 0, 0, 0, 0);
	}

	######################## level 2
	# part of handling "if" condition
	########################
	elsif (($line =~ /\bif\b/ || $line =~ /\belif\b/ || $line =~ /\belse\b/ || $in_if_condition == 1) 
		&& $line !~ /\".*if.*\"/ && $line !~ /\'.*if.*\'/ && $line !~ /\".*elif.*\"/ && $line !~ /\'.*elif.*\'/
		&& $line !~ /\".*else.*\"/ && $line !~ /\'.*else.*\'/
		&& $in_for_loop == 0 && $in_while_loop == 0 && $in_case == 0) {
		$in_if_condition = 1;
		if ($line !~ /\bfi\b/) {
			push @if_condition_stack, $line;
			my $current_index = get_index($line, @input_lines);
			if ($input_lines[$current_index + 1] =~ /\belif\b/ || $input_lines[$current_index + 1] =~ /\belse\b/) {
				handle_if_condition(\@if_condition_stack, 0, 0);
			}
		}
		elsif ($line =~ /\bfi\b/ ) {
			push @if_condition_stack, $line;
			if (count_leading_spaces($line) == 0) {
				$in_if_condition = 0;
				handle_if_condition(\@if_condition_stack, 0, 0, 0, 0);
			}
		}
	}

	######################## level 2
	# part of handling "test"
	########################
	elsif ($line !~ /$search_in_loop_key_words/ && $line !~ /$search_in_if_key_words/ 
		&& $line =~ /\btest\b/ && $line !~ /\bwhile\b/ && $line !~ /\bif\b/ && $line !~ /\belif\b/ 
		&& $line !~ /\".*test.*\"/ && $line !~ /\'.*test.*\'/ && $line !~ /test=|=test|\$test/ && $line !~ /test=|=test|\$test/
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		handle_test($line, 0, 0, 0, 0);
	}

	######################## level 3
	# part of handling "while" loop
	########################
	elsif (($line =~ /\bwhile\b/ || $in_while_loop == 1) && $line !~ /\".*while.*\"/ && $line !~ /\'.*while.*\'/
		&& $in_if_condition == 0 && $in_for_loop == 0 && $in_case == 0) {
		$in_while_loop = 1;
		if ($line !~ /\bdone\b/) {
			push @while_loop_stack, $line;
			next;
		}
		elsif ($line =~ /\bdone\b/) {
			push @while_loop_stack, $line;
			if (count_leading_spaces($line) == 0) {
				$in_while_loop = 0;
			}
			else {
				next;
			}
		}
		handle_while_loop(\@while_loop_stack, 0, 0, 0, 0);
	}

	######################## level 3
	# part of handling "comparison", this MUST be placed AFTER "handle_test"
	########################
	elsif ($line !~ /$search_in_loop_key_words/ && $line !~ /$search_in_if_key_words/ 
		&& $line =~ /\-eq |\-le |\-lt |\-ge |\-gt |\-ne |==|<=|>=|<|>/ 
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		handle_comparison($line, 0, 0, 0, 0);
	}

	######################## level 3
	# part of handling "expr"
	########################
	elsif ($line !~ /$search_in_loop_key_words/ && $line !~ /$search_in_if_key_words/ 
		&& $line =~ /\bexpr\b/ && $line !~ /\`.+\`/ && $line !~ /\".*expr.*\"/ && $line !~ /\'.*expr.*\'/ && $line !~ /expr=|=expr|\$expr/
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		handle_expr($line, 0, 0, 0, 0);
	}

	######################## level 4
	# part of handling "fgrep"
	########################
	elsif ($line !~ /$search_in_loop_key_words/ && $line !~ /$search_in_if_key_words/ 
		&& $line =~ /\bfgrep\b|grep -F/ && $line !~ /\".*fgrep.*\"/ && $line !~ /\'.*fgrep.*\'/ && $line !~ /fgrep=|=fgrep|\$fgrep/
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		handle_fgrep($line, 0, 0, 0, 0);
	}

	######################## level 4
	# part of handling "chmod"
	########################
	elsif ($line !~ /$search_in_loop_key_words/ && $line !~ /$search_in_if_key_words/ 
		&& $line =~ /\bchmod\b/ && $line !~ /\".*chmod.*\"/ && $line !~ /\'.*chmod.*\'/ && $line !~ /fgrep=|=fgrep|\$fgrep/
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0 && $in_case == 0) {
		handle_chmod($line, 0, 0, 0, 0);
	}

	######################## level 4
	# part of handling "case ... esac"
	########################
	elsif (($line =~ /\bcase\b.*\bin\b/ || $in_case == 1) 
		&& $in_if_condition == 0 && $in_for_loop == 0 && $in_while_loop == 0) {
		$in_case = 1;
		if ($line !~ /\besac\b/) {
			push @case_esac_stack, $line;
			next;
		}
		elsif ($line =~ /\besac\b/) {
			push @case_esac_stack, $line;
			if (count_leading_spaces($line) == 0) {
				$in_case = 0;
			}
			else {
				next;
			}
		}
		handle_case_esac(\@case_esac_stack, 0, 0, 0, 0);
	}

	# Lines we can't translate are turned into comments
	else {
		print "#$line\n";
	}
}

