#!/usr/bin/perl -w

push @level0_single_command_list, '\bls\b';
push @level0_single_command_list, '\bpwd\b';
push @level0_single_command_list, '\bid\b';
push @level0_single_command_list, '\bdate\b';
push @level0_single_command_list, '\brm\b';
push @level0_translate_command_list, '\bexit\b';
push @level0_translate_command_list, '\b"read\b';
push @level0_translate_command_list, '\bcd\b';
push @level0_translate_command_list, '\btest\b';
push @level0_translate_command_list, '\bexpr\b';
push @level0_translate_command_list, '\becho\b';
push @loop_key_words, '\bfor\b';
push @loop_key_words, '\bwhile\b';
#push @loop_key_words, '\bdo\b';
#push @loop_key_words, '\bdone\b';
push @if_key_words, '\bif\b';
push @if_key_words, '\belse\b';
push @if_key_words, '\belif\b';
#push @if_key_words, '\bthen\b';
#push @if_key_words, '\bfi\b';

# used for a quicker key-word search
$search_in_single_commands = join("|", @level0_single_command_list);
$search_in_translate_commands = join("|", @level0_translate_command_list);
$search_in_loop_key_words = join("|", @loop_key_words);
$search_in_if_key_words = join("|", @if_key_words);

while ($line = <>) {
	chomp $line;
	push @input_lines, $line;
}

$in_for_loop = 0;
$in_while_loop = 0;
$in_if_condition = 0;
@for_loop_stack = ();
@while_loop_stack = ();
@if_condition_stack = ();

###################################################################
#								  #
# 			functional functions 			  #
#								  #
###################################################################
sub check_import_libraries { # check import libraries and displayed firstly
	my @import_list;
	foreach my $line (@input_lines) {
		if ($line =~ /$search_in_single_commands|\brm\b|\btrue\b|\bfgrep\b/) {
			if (!("import subprocess\n" ~~ @import_list)) {
				push @import_list, "import subprocess\n";
			}
		}
		elsif ($line =~ /\-d {1}/) {
			if (!("import os.path\n" ~~ @import_list)) {
				push @import_list, "import os.path\n";
			}
		}
		elsif ($line =~ /cd|\-r {1}/) {
			if (!("import os\n" ~~ @import_list)) {
				push @import_list, "import os\n";
			}
		}
		elsif ($line =~ /exit|read|\$[0-9]+|\$\@|\$\#/) {
			if (!("import sys\n" ~~ @import_list)) {
				push @import_list, "import sys\n";
			}
		}
		elsif ($line =~ /\*\.[A-Za-z]+/) {
			if (!("import glob\n" ~~ @import_list)) {
				push @import_list, "import glob\n";
			}
		}
	}
	print @import_list;
}

sub get_index { # get index of a specific $line from the array
	while (@_) {
		return @_-1 if $_[0] eq pop
	}
}

sub count_leading_spaces { # count the spaces in front of the string ($tabs)
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
	return $number_of_tabs;
}

###################################################################
#								  #
# 			  level 0 functions 			  #
#								  #
###################################################################

######################## level 0 / level 1 / level 2 / level 3
# handle_echo
########################
sub handle_echo {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp $line;
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}
	
	my @words = split / /, $line;
	if ($words[1] eq '-n') { # echo with option n, without trailing newline
		if ($words[2] =~ /\".+/) {
			print "print";
			foreach my $word (@words[2 .. $#words]) {
				$word = handle_variable($word, 0, 0);
				print " $word";
			}
		}
		elsif ($words[2] =~ /\'.+/) {
			print "print";
			foreach my $word (@words[2 .. $#words]) {
				print " $word";
			}
		}
		else {
			if ($words[2] =~ /\$/) { # is a variable
				$words[2] =~ s/\$//g;
				print "print $words[2]";
			}
			else {
				print "print \'$words[2]\'";
			}
			foreach my $word (@words[3 .. $#words]) {
				print ", ";
				if ($word =~ /\$/) { # is a variable
					$word =~ s/\$//g;
					if ($word =~ /[0-9]+/) { #is a variable, and it's an index of argv
						print "sys.argv[$word]"

					}
					else {
						print "$word";
					}	
				}
				else {
					print "\'$word\'";
				}
			}
		}
		print ",";
	}
	else { #echo without option n, with trailing newline
		if ($words[1] =~ /\".+/) {
			print "print";
			foreach my $word (@words[1 .. $#words]) {
				$word = handle_variable($word, 0, 0);
				print " $word";
			}
		}
		elsif ($words[1] =~ /\'.+/) {
			print "print";
			foreach my $word (@words[1 .. $#words]) {
				print " $word";
			}
		}
		else {
			if ($words[1] =~ /\$/) { # is a variable
				$words[1] =~ s/\$//g;
				print "print $words[1]";
			}
			else {
				print "print \'$words[1]\'";
			}
			foreach my $word (@words[2 .. $#words]) {
				print ", ";
				if ($word =~ /\$/) { # is a variable
					$word =~ s/\$//g;
					if ($word =~ /[0-9]+/) { #is a variable, and it's an index of argv
						print "sys.argv[$word]"

					}
					else {
						print "$word";
					}	
				}
				else {
					print "\'$word\'";
				}
			}
		}
		if (!$isif && !$iscomment && !$iswhile) {
			print "\n";
		}
	}
}

######################## level 0 / level 3 / level 4
# handle_simple_command
########################
sub handle_simple_command {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp $line;
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}

	my $isend = 0;
	my @words = split / /, $line;
	if ($words[0] =~ /\btrue\b/) {
		print "not subprocess.call([\'$words[0]\'])";
		$isend = 1;
	}
	elsif ($words[0] =~ /\bfalse\b/) {
		print "not subprocess.call([\'$words[0]\'])";
		$isend = 1;
	}
	else {
		print "subprocess.call([\'$words[0]\'";	
	}
	foreach my $word (@words[1 .. $#words]) {
		if ($word !~ /\$/) { # $word is not a variable
			print ", ";
			print "\'$word\'";
		}
		else { # $word is a variable
			if ($word =~ /\$[^\@\#\$\%\&\*]/) { # $word is a normal variable
				$word = handle_variable($word, 0, 0, 0);
				print ", ";
				print "str($word)";
			}
			else {
				$word = handle_variable($word, 0, 0, 0);
				print "] + ";
				print "$word";
				print ")";
				$isend = 1;
			}
		}
	}
	if (!$isend) {
		print "])";
	}
	if (!$isif && !$iscomment && !$iswhile) {
		print "\n";
	}
}

######################## level 0 / level 3
# handle_simple_variable
########################
sub handle_simple_variable {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp $line;
	$line =~ s/\s+&//g;
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}
	my @words = split /=/, $line; # a line with simple variables only has two elements: variable, and value

	if ($words[1] =~ /\$/) { # is a variable or string contains a variable
		$words[1] = handle_variable($words[1], 0, 0);
		print "$words[0] = $words[1]";
	}
	elsif ($words[1] =~ /[0-9]+/ && $words[1] !~ /\$/) {
		print "$words[0] = $words[1]";
	}
	else { # not a variable
		print "$words[0] = \'$words[1]\'";
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
	chomp $line;
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
########################
sub handle_for_loop {
	my ($stack, $tabs, $isif, $iscomment, $iswhile) = @_;
	my @for_stack = @$stack;
	@for_loop_stack = ();
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}

	my @words = split / /, $for_stack[0];
	# store the variable name and values in for loop
	my $variable = $words[1];
	my @values = ();
	foreach my $value (@words[3 .. $#words]) {
		push @values, $value;
	}

	print "for $variable in ";
	if ($values[0] =~ /\*\.[A-Za-z]+/) { # the variable is in files
		print "sorted(glob.glob(\"$values[0]\"):\n";
	}
	else {
		if ($values[0] !~ /[0-9]+/) {
			print "\'$values[0]\'";
		}
		else {
			print "$values[0]";
		}
		foreach my $value (@values[1 .. $#values]) {
			print ", ";
			if ($value !~ /[0-9]+/) {
				print "\'$value\'";
			}
			else {
				print "$value";
			}
		}
		print ":\n";
	}

	# handle the rest of the lines in the for stack
	foreach my $line (@for_stack[2 .. $#for_stack]) {
		$tabs = count_leading_spaces($line);
		chomp $line;
		$line =~ s/^\s*//;
		if ($line =~ /\bdone\b/) {
			last;
		}
		else {
			check_line($line, $tabs, $isif, $iscomment, $iswhile);
		}
	}
}

######################## level 1
# handle_exit
########################
sub handle_exit {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp $line;
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
	chomp $line;
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
########################
sub handle_if_condition {
	my ($stack, $tabs, $isif, $iscomment, $iswhile) = @_;
	my @if_stack = @$stack;
	@if_condition_stack = ();
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}

	# handle the first line, like "if test this_assignment = damn" or "elif test this_assignment = samn"
	my @syntax_first_line = ();
	my @words = split / /, $if_stack[0];
	foreach my $word (@words[1 .. $#words]) {
		push @syntax_first_line, $word;
	}
	my $syntax_string = join(" ", @syntax_first_line);
	if ($words[0] =~ /\bif\b/) {	
		print "if ";
	}
	elsif ($words[0] =~ /\belif\b/) {
		print "elif ";
	}
	elsif ($words[0] =~ /\belse\b/) {
		print "else:\n";
	}
	if ($words[0] =~ /\bif\b/ || $words[0] =~ /\belif\b/) {
		my $isif = 1;
		if ($syntax_string =~ /\[|\]/) {
			handle_bracket($syntax_string, $tabs, $isif, $iscomment, $iswhile);
		}
		else {
			check_line($syntax_string, $tabs, $isif, $iscomment, $iswhile);
		}
		print ":\n";
	}

	# handle the rest of the lines in the stack
	my $index = 2;
	if ($words[0] =~ /\belse\b/) {	
		$index = 1;
	}
	foreach my $line (@if_stack[$index .. $#if_stack]) {
		$tabs = count_leading_spaces($line);
		chomp $line;
		$line =~ s/^\s*//;
		if ($line =~ /\bfi\b/) {
			last;
		}
		else {
			check_line($line, $tabs, 0, 0);
		}
	}
}

######################## level 2 / level 3
# handle_test
########################
sub handle_test {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp $line;
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}

	my @words = split / /, $line;
	if ($line =~ /\=/) { # a variable and a value
		my $variable = $words[1];
		my $value = $words[3];

		if ($variable =~ /\$/) { # variable is a "variable"
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
				if ($value =~ /[0-9]+/) {
					print "$variable == $value";
				}
				else {
					print "$variable == \'$value\'";
				}
			}
		}
		else { # variable is a "string" or "number", not a "variable"
			if ($variable =~ /[0-9]+/) {
				if ($value =~ /[0-9]+/) {
					print "$variable == $value";
				}
				else {
					print "$variable == \'$value\'";
				}
			}
			else {
				if ($value =~ /[0-9]+/) {
					print "\'$variable\' == $value";
				}
				else {
					print "\'$variable\' == \'$value\'";
				}
			}
		}
	}
	elsif ($line =~ /\-[a-z]{1} {1}/) { # the $line is a test command with options
		my $file = $words[2];
		if ($line =~ /\-r/) { # try to reach a file/directory
			print "os.access(\'$file\', os.R_OK)";
		}
		elsif ($line =~ /\-d/) { # try to detect whether is a directory
			print "os.path.isdir(\'$file\')";
		}
	}
	elsif ($line =~ /\-eq|\-le|\-lt|\-ge|\-gt|\-ne/) { # comparison
		my @syntaxs = ();
		my $compare = $words[2];
		my $left = $words[1];
		my $right = $words[3];
		$left = handle_variable($left, 0, 0);
		$right = handle_variable($right, 0, 0);
		push @syntaxs, $left;
		push @syntaxs, $compare;
		push @syntaxs, $right;
		my $comparison_syntax = join(" ", @syntaxs);
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
########################
sub handle_variable {
	my ($word, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp $word;
	if ($word =~ /\$/ && $word !~ /\`.+\`/) { # variables without back quotes
		$word =~ s/^\$//;
		if ($word =~ /\@/) { # a system variable
			return "sys.argv[1:]";
		}
		elsif ($word =~ /\#/) { # a system variable
			return "len(sys.argv[1:])";
		}
		elsif ($word =~ /^[0-9]+/) { # a system variable too
			$word =~ s/\"//g;
			return "sys.argv[$word]";
		}
		elsif ($word =~ /^\(.+\)/) { # variable is a syntax's result
			$word =~ s/^\(//;
			$word =~ s/\)$//;
			my $expr = handle_expr($word, 0, 0, 0, 0);
			return $expr;
		}
		else { # a named variable
			$word =~ s/\"//g;
			$word =~ s/\$//g;
			return $word;
		}
	}
	elsif ($word =~ /\`.+\`/) { # variables in back quotes
		$word =~ s/\`//g;
		if ($word =~ /expr/) {
			$word = handle_expr($word);
			return $word;
		}
		else {
			return "\'$word\'";
		}
	}
	else { # not a variable
		return $word;
	}
}

######################## level 3
# handle_while_loop
########################
sub handle_while_loop {
	my ($stack, $tabs, $isif, $iscomment, $inwhile) = @_;
	my @while_stack = @$stack;
	@while_loop_stack = ();
	for (my $i = 0; $i < $tabs; $i ++) {
		print " ";
	}
	my @words = split / /, $while_stack[0];
	# handle the first line, like "while test this_assignment -eq damn"
	my @syntax_first_line = ();
	foreach my $word (@words[1 .. $#words]) {
		push @syntax_first_line, $word;
	}
	my $syntax_string = join(" ", @syntax_first_line);
	print "while ";
	my $iswhile = 1;
	if ($syntax_string =~ /\[|\]/) {
		handle_bracket($syntax_string, $tabs, $isif, $iscomment, $iswhile);
	}
	else {
		check_line($syntax_string, $tabs, $isif, $iscomment, $iswhile);
	}
	print ":\n";

	# handle the loop
	foreach my $line (@while_stack[2 .. $#while_stack]) {
		$tabs = count_leading_spaces($line);
		chomp $line;
		$line =~ s/^\s*//;
		if ($line =~ /\bdone\b/) {
			last;
		}
		else {
			check_line($line, $tabs, 0, $iscomment, 0);
		}
	}
}

######################## level 3
# handle_comparison
########################
sub handle_comparison {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp $line;
	my @words = split / /, $line;
	my $compare = $words[1];
	my $left = $words[0];
	my $right = $words[2];
	$left = handle_variable($left, 0, 0);
	$right = handle_variable($right, 0, 0);
	if ($left !~ /^[0-9]+$/ && $left !~ /len\(.+\)/) {
		$left = "int($left)";
	}
	if ($right !~ /^[0-9]+$/ && $right !~ /len\(.+\)/) {
		$right = "int($right)";
	}
	if ($compare =~ /\-eq/) {
		print "$left == $right";
	}
	elsif ($compare =~ /\-le/) {
		print "$left <= $right";
	}
	elsif ($compare =~ /\-lt/) {
		print "$left < $right";
	}
	elsif ($compare =~ /\-ge/) {
		print "$left >= $right";
	}
	elsif ($compare =~ /\-gt/) {
		print "$left > $right";
	}
	elsif ($compare =~ /\-ne/) {
		print "$left != $right";
	}
}

######################## level 3
# handle_expr
########################
sub handle_expr {
	my ($syntax, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp $syntax;

	$syntax =~ s/^\(//;
	$syntax =~ s/\)$//;
	@words = split(/ /, $syntax);
	my @result = ();
	my $index = 0;

	if ($syntax =~ /expr/) {
		$index = 1;
	}
	foreach my $word (@words[$index .. $#words]) {
		if ($word =~ /\$/) { # a variable
			$word =~ s/\$//;
			if ($word =~ /\@/) {
				push @result, "sys.argv[1:]";
			}
			elsif ($word =~ /^[0-9]+/) {
				$word =~ s/\"//g;
				push @result, "sys.argv[$word]";
			}
			else {
				$word =~ s/\"//g;
				push @result, "int($word)";
			}
		}
		elsif ($word =~ /[0-9]+/ && $word !~ /\$/) {
			push @result, $word;
		}
		elsif ($word =~ /\*|\+|\%|\-|\//) {
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
	chomp $line;
	$line =~ s/\[//g;
	$line =~ s/\]//g;
	$line =~ s/^ +//g;
	$line =~ s/ +$//g;
	if ($line =~ /\-eq|\-le|\-lt|\-ge|\-gt|\-ne/ ) {
		handle_comparison($line, $tabs, $isif, $iscomment, $iswhile);
	}
	elsif ($line =~ /\-[a-z]{1} {1}/) { # the $line is with options
		my @words = split(/ /, $line);
		my $file = $words[1];
		if ($line =~ /\-r/) { # try to reach a file/directory
			print "os.access(\'$file\', os.R_OK)";
		}
		elsif ($line =~ /\-d/) { # try to detect whether is a directory
			print "os.path.isdir(\'$file\')";
		}
	}
	if (!$isif && !$iscomment && !$iswhile) {
		print "\n";
	}
}

###################################################################
#								  #
# 			    sub loop 				  #
#								  #
###################################################################
sub check_line {
	my ($line, $tabs, $isif, $iscomment, $iswhile) = @_;
	chomp $line;
	my $in_for_loop = 0;
	my $in_while_loop = 0;
	my $in_if_condition = 0;

	if ($line =~ /^ *$/ && $in_for_loop == 0 && $in_while_loop == 0) {
		print "\n";
	}

	elsif ($line =~ /^#[^!]{1}.*/ && $in_for_loop == 0 && $in_while_loop == 0) {
		print "$line\n";
	}

	elsif ($line =~ /.+[^\$]#.+/) { # use recursion to handle lines containing comments
		my $iscomment = 1;
		my @sublines = split(/#/, $line);
		chomp(@sublines);
		my $left = $sublines[0];
		my $right = $sublines[1];
		$left =~ s/ +$//;
		check_line($left, $tabs, $isif, $iscomment, $iswhile);
		print " #$right\n";
	}

	######################## level 0
	# part of handling "echo"
	########################
	elsif ($line =~ /\becho\b/ && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		handle_echo($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 0
	# part of handling simple builtin commands and boolean, which needs subprocess in python
	########################
	elsif ($line =~ /$search_in_single_commands|\btrue\b|\bfalse\b/ && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		handle_simple_command($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 0
	# part of handling simple variables, line only contains variables
	########################
	elsif ((($line !~ /$search_in_single_commands/ 
		&& $line !~ /$search_in_translate_commands/ 
		&& $line !~ /$search_in_loop_key_words/ 
		&& $line !~ /$search_in_if_key_words/) || $line =~ /\`.+\`/) 
		&& $line =~ /\=/ && $in_for_loop == 0 
		&& $in_if_condition == 0 && $in_while_loop == 0) {
		handle_simple_variable($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 1
	# part of handling "cd"
	########################
	elsif ($line =~ /\bcd\b/ && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		handle_cd($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 1
	# part of handling "for" loop
	########################
	elsif (($line =~ /\bfor\b/ || $in_for_loop == 1) && $in_if_condition == 0 && $in_while_loop == 0) {
		$in_for_loop = 1;
		if ($line !~ /\bdone\b/) {
			push @for_loop_stack, $line;
			next;
		}
		elsif ($line =~ /\bdone\b/) {
			push @for_loop_stack, $line;
			$in_for_loop = 0;
		}
		handle_for_loop(\@for_loop_stack, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 1
	# part of handling "exit"
	########################
	elsif ($line =~ /\bexit\b/ && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		handle_exit($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 1
	# part of handling "read"
	########################
	elsif ($line =~ /\bread\b/ && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		handle_read($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 2
	# part of handling "if" condition
	########################
	elsif (($line =~ /\bif\b/ || $line =~ /\belif\b/ || $line =~ /\belse\b/ || $in_if_condition == 1) 
		&& $in_for_loop == 0 && $in_while_loop == 0) {
		$in_if_condition = 1;
		if ($line !~ /\bfi\b/) {
			push @if_condition_stack, $line;
			my $current_index = get_index($line, @input_lines);
			if ($input_lines[$current_index + 1] =~ /\belif\b/ || $input_lines[$current_index + 1] =~ /\belse\b/) {
				handle_if_condition(\@if_condition_stack, $tabs, $isif, $iscomment, $iswhile);
			}
		}
		elsif ($line =~ /\bfi\b/ ) {
			push @if_condition_stack, $line;
			$in_if_condition = 0;
			handle_if_condition(\@if_condition_stack, $tabs, $isif, $iscomment, $iswhile);
		}
	}
	
	######################## level 2
	# part of handling "test"
	########################
	elsif ($line =~ /\btest\b/ && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		handle_test($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 3
	# part of handling "while" loop
	########################
	elsif (($line =~ /\bwhile\b/ || $in_for_loop == 1) && $in_if_condition == 0 && $in_for_loop == 0) {
		$in_while_loop = 1;
		if ($line !~ /\bdone\b/) {
			push @while_loop_stack, $line;
			next;
		}
		elsif ($line =~ /\bdone\b/) {
			push @while_loop_stack, $line;
			$in_while_loop = 0;
		}
		handle_while_loop(\@while_loop_stack, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 3
	# part of handling "comparison", this MUST be placed AFTER "handle_test"
	########################
	elsif ($line =~ /\-eq|\-le|\-lt|\-ge|\-gt|\-ne/ 
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		handle_comparison($line, $tabs, $isif, $iscomment, $iswhile);
	}

	######################## level 3
	# part of handling "expr"
	#########[ -d /dev/null ]###############
	elsif ($line =~ /\bexpr\b/ && $line !~ /\`.+\`/ 
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		handle_expr($line, $tabs, $isif, $iscomment, $iswhile);
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
foreach my $line (@input_lines) {

	# part of program declaration
	if ($line =~ /^#!\// && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) { # && $. == 1
		print "#!/usr/bin/python2.7 -u\n";
		check_import_libraries();
	}

	elsif ($line =~ /^\s*$/ && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		print "\n";
	}

	elsif ($line =~ /^#[^!]{1}.*/ && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		print "$line\n";
	}
	
	######################## level 0
	# part of handling "echo"
	# part of handling "echo -n"
	# part of handling "echo" variables
	########################
	elsif ($line =~ /\becho\b/ && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		handle_echo($line, 0, 0, 0, 0);
	}

	######################## level 0
	# part of handling simple builtin commands, which needs subprocess in python
	########################
	elsif ($line =~ /$search_in_single_commands/ && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		handle_simple_command($line, 0, 0, 0, 0);
	}

	######################## level 0
	# part of handling simple variables, line only contains variables
	########################
	elsif ((($line !~ /$search_in_single_commands/ 
		&& $line !~ /$search_in_translate_commands/ 
		&& $line !~ /$search_in_loop_key_words/ 
		&& $line !~ /$search_in_if_key_words/) || $line =~ /\`.+\`/) 
		&& $line =~ /\=/ && $in_for_loop == 0 
		&& $in_if_condition == 0 && $in_while_loop == 0) {
		handle_simple_variable($line, 0, 0, 0, 0);
	}

	######################## level 1
	# part of handling "cd"
	########################
	elsif ($line =~ /\bcd\b/ && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		handle_cd($line, 0, 0, 0, 0);
	}

	######################## level 1
	# part of handling "for" loop
	########################
	elsif (($line =~ /\bfor\b/ || $in_for_loop == 1) && $in_if_condition == 0 && $in_while_loop == 0) {
		$in_for_loop = 1;
		if ($line !~ /\bdone\b/) {
			push @for_loop_stack, $line;
			next;
		}
		elsif ($line =~ /\bdone\b/) {
			push @for_loop_stack, $line;
			$in_for_loop = 0;
		}
		handle_for_loop(\@for_loop_stack, 0, 0, 0, 0);
	}

	######################## level 1
	# part of handling "exit"
	########################
	elsif ($line =~ /\bexit\b/ && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		handle_exit($line, 0, 0, 0, 0);
	}

	######################## level 1
	# part of handling "read"
	########################
	elsif ($line =~ /\bread\b/ && $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		handle_read($line, 0, 0, 0, 0);
	}

	######################## level 2
	# part of handling "if" condition
	########################
	elsif (($line =~ /\bif\b/ || $line =~ /\belif\b/ || $line =~ /\belse\b/ || $in_if_condition == 1) 
		&& $in_for_loop == 0 && $in_while_loop == 0) {
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
			$in_if_condition = 0;
			handle_if_condition(\@if_condition_stack, 0, 0, 0, 0);
		}
	}

	######################## level 2
	# part of handling "test"
	########################
	elsif ($line =~ /\btest\b/ && $line !~ /\bwhile\b/ 
		&& $line !~ /\bif\b/ && $line !~ /\belif\b/ 
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		handle_test($line, 0, 0, 0, 0);
	}

	######################## level 3
	# part of handling "while" loop
	########################
	elsif (($line =~ /\bwhile\b/ || $in_while_loop == 1) && $in_if_condition == 0 && $in_for_loop == 0) {
		$in_while_loop = 1;
		if ($line !~ /\bdone\b/) {
			push @while_loop_stack, $line;
			next;
		}
		elsif ($line =~ /\bdone\b/) {
			push @while_loop_stack, $line;
			$in_while_loop = 0;
		}
		handle_while_loop(\@while_loop_stack, 0, 0, 0, 0);
	}

	######################## level 3
	# part of handling "comparison", this MUST be placed AFTER "handle_test"
	########################
	elsif ($line =~ /\-eq|\-le|\-lt|\-ge|\-gt|\-ne/ 
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		handle_comparison($line, 0, 0, 0, 0);
	}

	######################## level 3
	# part of handling "expr"
	########################
	elsif ($line =~ /\bexpr\b/ && $line !~ /\`.+\`/ 
		&& $in_for_loop == 0 && $in_if_condition == 0 && $in_while_loop == 0) {
		handle_expr($line, 0, 0, 0, 0);
	}

	# Lines we can't translate are turned into comments
	else {
		print "#$line\n";
	}
}

