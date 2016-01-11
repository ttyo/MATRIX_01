#!/usr/bin/perl -w

# written by andrewt@cse.unsw.edu.au September 2015
# as a starting point for COMP2041/9041 assignment 2
# http://cgi.cse.unsw.edu.au/~cs2041/assignments/bitter/

use CGI qw/:all/;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;


sub main()
{
	# print start of HTML ASAP to assist debugging if there is an error in the script
	print page_header();

	# Now tell CGI::Carp to embed any warning in HTML
	warningsToBrowser(1);

	# define some global variables
	$debug = 1;
	$dataset_size = "small";
	$users_dir = "dataset-$dataset_size/users";
	$bleats_dir = "dataset-$dataset_size/bleats";

	print user_page();
	print page_trailer();
}


#
# Show unformatted details for user "n".
# Increment parameter n and store it as a hidden variable
#
sub user_page
{
	my $n = param('n') || 0; # index
	my @users = sort(glob("$users_dir/*")); # array of usernames
	my $user  = $users[$n % @users]; # a single user name
	my $user_info_file = "$user/details.txt";
	my $user_bleat_file = "$user/bleats.txt";
	my @user_info_lines;

	open my $U, "$user_info_file" or die "can not open $user_info_file: $!"; # read the content of user information file
	$user_info = join '', <$U>;
	@user_info_lines = <$U>;
	close $U;

	open my $B, "$user_bleat_file" or die "can not open $user_bleat_file: $!"; # read the content of user bleat index file
	$user_bleat_index = join '-', <$B>;
	close $B;

	my @bleat_file_array = split /-/, $user_bleat_index; # array stores all the bleat index of a user, each element is the name of bleat file
	my @user_all_bleat = ();
	for my $file (@bleat_file_array)
	{
		$file = "$bleats_dir/$file";
		open my $B, "$file" or die "can not open $file: $!";
		my $bleat_content = join '', <$B>;
		push @user_all_bleat, $bleat_content;
	}
	my $next_user = $n + 1;



	print start_form, "\n";
	print "Username:\n", textfield('username'), "\n";
	print "Password:\n", textfield('password'), "\n";
	print submit(value => Login), "\n";
	print end_form, "\n";




	return <<eof
<div class="bitter_user_details">
$user_info
@user_all_bleat
</div>
<p>
<form method="POST" action="">
<input type="hidden" name="n" value="$next_user">
<input type="submit" value="Next user" class="bitter_button">
</form>
eof
}


#
# HTML placed at the top of every page
#
sub page_header
{
	return <<eof
Content-Type: text/html

<!DOCTYPE html>
<html lang="en">
<head>
<title>Bitter</title>
<link href="bitter.css" rel="stylesheet">
</head>
<body>
<div class="bitter_heading">
Bitter
</div>
eof
}


#
# HTML placed at the bottom of every page
# It includes all supplied parameter values as a HTML comment
# if global variable $debug is set
#
sub page_trailer {
	my $html = "";
	$html .= join("", map("<!-- $_=".param($_)." -->\n", param())) if $debug;
	$html .= end_html;
	return $html;
}

main();



