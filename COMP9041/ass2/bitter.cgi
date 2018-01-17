#!/usr/bin/perl -w

use CGI qw/:all/;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;
use File::Copy;

sub main()
{
	# print start of HTML ASAP to assist debugging if there is an error in the script
	print page_header();

	# Now tell CGI::Carp to embed any warning in HTML
	warningsToBrowser(1);

	# define some global variables
	$debug = 1;
	$dataset_size = "medium";
	$users_dir = "dataset-$dataset_size/users";
	$bleats_dir = "dataset-$dataset_size/bleats";
	$suspend_dir = "dataset-$dataset_size/suspend";
	$notification_dir = "dataset-$dataset_size/notification";

	print user_page();
	print page_trailer();
}


#
# Show unformatted details for user "n".
# Increment parameter n and store it as a hidden variable
#
sub user_page
{
	my $username = param('username') || '';
	my $password = param('password') || '';
	my $search = param('search') || '';
	my $send_bleat = param('send_bleat') || '';
	my $reply_bleat = param('reply_bleat') || '';
	my $search = param('search') || '';
	my $add_listen = param('add_listen') || '';
	my $rm_listen = param('rm_listen') || '';
	my $search_bleat = param('search_bleat') || '';
	my $checked_bleat = param('checked_bleat') || '';
	my $delete_bleat = param('delete_bleat') || '';
	my $create_account = param('create_account') || '';
	my $create_username = param('create_username') || '';
	my $create_password = param('create_password') || '';
	my $create_email = param('create_email') || '';
	my $create_profile = param('create_profile') || '';
	my $original_username = param('original_username') || '';
	my $original_email = param('original_email') || '';
	my $manage_account = param('manage_account') || '';

	my $display = "<div class=\"bitter_heading\">Welcome to Bitter, a website bitter than both facebook and twitter!</div>";
	my $display_bleat = '';

	if ($username && ($password || param('back')) && !defined param("logout")) # user login, when press "back" button, pass the password check
	{
		$username =~ s/ +//g;
		my $n = param('n') || 0; # index
		my $user = glob("$users_dir/$username"); # path of the specific username
		my $user_detail_file = "$user/details.txt"; # dataset-small/users/xxxxx/details.txt
		my $user_bleat_file = "$user/bleats.txt"; # dataset-small/users/xxxxx/bleats.txt
		my $suspend_detail_file = "$suspend_dir/$username/details.txt"; # dataser-small/suspend/xxxxx/details.txt
		my $suspend_bleat_file = "$suspend_dir/$username/bleats.txt";
		my @user_info_lines;
		my $pwd;
		my $user_image = "$user/profile.jpg";
		my $suspend_image = "$suspend_dir/$username/profile.jpg";
		my %bleat_all;
		my @my_listens;
		my $U;
		my $suspend = 0;
		my $active = 0;

		if (!open $U, "<$user_detail_file") # cannot open userfile
		{
			if (!open $U, "<$suspend_detail_file") # cannot open suspend userfile
			{
				$display = "Unknown username: $username\n";
				print start_form, "\n";
				print "Username:\n", textfield('username'), "\n";
				print "Password:\n", textfield('password'), "\n";
				print submit(value => Login), "\n";
				print "<a href=\"bitter.cgi?recover_account=
					1\"> Forgot your password?</a>";
				print end_form, "\n";
				print start_form, "\n";
				print "No account? Why not<a href=\"bitter.cgi?create_account=
					1\"> create an account</a> now, making your friends know you're a Bitter guy!";
				print end_form, "\n";
			}
			else # open the suspend userfile
			{
				$suspend = 1; # acconut suspended tag
			}
		}
		else
		{
			$active = 1; # account active tag
		}

		if ($suspend || $active) # one of the userfile opened
		{
			my @display_content;
			my @user_content = <$U>;
			for (@user_content)
			{
				if ($_ =~ /password:/i) # get password and go to next
				{
					$pwd = $_;
					$pwd =~ s/ *password: *//ig;
					$pwd =~ s/ +$//g;
					chomp($pwd);
					next;
				}
				elsif ($_ =~ /email:/i) # not display email
				{
					next;
				}
				else
				{
					if ($_ =~ /listens:/i) # get the listens
					{
						my $listen = $_;
						chomp($listen);
						$listen =~ s/ *listens: *//i;
						$listen =~ s/ +/ /g;
						@my_listens = split / /, $listen;
					}
					else
					{
						push @display_content, $_;
					}
				}
			}
			if ($pwd =~ /^$password$/ || param('back')) #QUESTION, "==" NOT WORK, password match, user now is login
			{
				#
				# part of displaying user information and avatar
				#
				my $image = '';
				if (!$suspend) # is the user acconut is active
				{
					if (-e $user_image)
					{
						$image = "<img src=\"$user_image\" style=\"width:256px;height:256px;\">\n"
					}
					else
					{
						$image = "(no user avatar)\n";
					}
					$display = "<div class=\"bitter_heading\">User login as: $username</div>";
					$display = "${display}$image<a href=\"bitter.cgi?manage_image=1&login_name=$username\">Manage Your Avatar</a>";
					$display = "${display}   <a href=\"bitter.cgi?manage_account=1&login_name=$username\">Manage Your Account</a>\n";
				}
				else # if the user account is suspended
				{
					if (-e $suspend_image)
					{
						$image = "<img src=\"$suspend_image\" style=\"width:256px;height:256px;\">\n"
					}
					else
					{
						$image = "(no user avatar)\n";
					}
					$display = "<div class=\"bitter_heading\">User login as: $username (Suspending)</div>
						<div class=\"bitter_heading\">(Attention: you can not send/receive/delete bleats and manage your account under suspending)</div>\n$image";
				}

				my $temp = join '', @display_content;
				$display = "${display}$temp\nCurrent listens: ";
				if (scalar(@my_listens) < 1)
				{
					push @my_listens, "(no listens)";
				}
				foreach my $listen (@my_listens)
				{
					$display = "${display}$listen / ";
				}
				$display = "${display}\n";

				#
				# part of displaying bleat information and other bleats from listens or with @user
				#
				my $B;
				if (!$suspend)
				{
					open $B, "$user_bleat_file" or die "can not open $user_bleat_file: $!"; # read the content of user bleat index file
				}
				else
				{
					open $B, "$suspend_bleat_file" or die "can not open $suspend_bleat_file: $!"; # read the content of user bleat index file
				}
				my @user_bleat_file_list = <$B>;
				for (@user_bleat_file_list) # read bleats from user
				{
					my $filename = $_;
					my $time_of_bleat;
					my $file_of_bleat = "$bleats_dir/$_";
					open my $F, "$file_of_bleat" or die "can not open $file_of_bleat: $!";
					my @lines = <$F>;
					my @temp_lines = ();
					my $tag;
					for (@lines)
					{
						if ($_ =~ /latitude:/i)
						{
							next;
						}
						elsif ($_ =~ /longitude:/i)
						{
							next;
						}
						elsif ($_ =~ /in_reply_to:/i)
						{
							next;
						}
						elsif ($_ =~ /username:/i)
						{
							next;
						}
						elsif ($_ =~ /##[0-9]+##/) # has attachment
						{
							$tag = $_;
							$tag =~ s/\#+//g;
							next;
						}
						else
						{
							my $line = $_;
							if ($line =~ /time:/i)
							{
								$time_of_bleat = $line;
								$time_of_bleat =~ s/ *time: *//ig;
								$time_of_bleat =~ s/ +$//g;
								chomp($time_of_bleat);
							}
							if ($line =~ /bleat:/i)
							{
								chomp($line);
								$line =~ s/bleat: +//;
								if (!$suspend)
								{
									$line = "<a href=\"bitter.cgi?click_bleat=$filename&login_name=$username\">$line</a>      <a href=\"bitter.cgi?delete_bleat=
										$filename&login_name=$username\">[Delete]</a>\n";
								}
								else
								{
									$line = "$line\n";
								}
							}
							push @temp_lines, $line;
						}
					}
					if ($tag)
					{
						if (!$suspend)
						{
							my $image = "$user/attachment/$tag.jpg";
							push @temp_lines, "<img src=\"$image\" style=\"width:256px;height:256px;\">\n";	
						}
						else
						{
							my $image = "$suspend_dir/$username/attachment/$tag.jpg";
							push @temp_lines, "<img src=\"$image\" style=\"width:256px;height:256px;\">\n";	
						}
					}
					push @temp_lines, "#";
					my $bleat_content = join '', @temp_lines;
					$bleat_all{$time_of_bleat} = $bleat_content; # store the bleat content in hash table based on bleat time
				}
				my @temp_lines_notification;
				my @notification;
				if (-e "$notification_dir/$username")
				{
					@notification = sort(glob("$notification_dir/$username/*"))
				}
				my $nsize = @notification;
				if ($nsize != 0)
				{
					$display_bleat = "<div class=\"bitter_heading\">Some Bitter guys replied/marked you!</div>";
					my @sender;
					my @bleat_number;
					for (@notification)
					{
						open my $F, "$_" or die "can not open $_: $!";
						my @noti_content = <$F>;
						my $mark;
						my $file = $_;
						$file =~ s/^.*$username\///;
						for (@noti_content)
						{
							if ($_ =~ /username:/) # check the sender
							{
								$mark = $_;
								chomp($mark);
								$mark =~ s/username://;
								$mark =~ s/ +//g;
							}
						}
						if ($mark)
						{
							push @sender, $mark;
							push @bleat_number, $file;
						}
					}
					my $size = @sender;
					for (my $i = 0; $i < $size; $i ++)
					{
						my $string = "From $sender[$i], bleat number: <a href=\"bitter.cgi?click_bleat=$bleat_number[$i]&login_name=$username&notification=1\">$bleat_number[$i]</a>\n";
						push @temp_lines_notification, $string;
					}
					my $result_content = join "#\n", @temp_lines_notification;
					$display_bleat = "${display_bleat}<div class=\"bitter_bleat_details\">$result_content</div>";
				}

				my @temp_result = ();
				foreach my $time (reverse sort keys %bleat_all) # sort the hash table based on bleat time
				{
					push @temp_result, "\n$bleat_all{$time}";
				}
				$display_bleat = "${display_bleat}<div class=\"bitter_heading\">Bleats from user: $username</div>";
				if (!$suspend)
				{
					$display_bleat = "${display_bleat}<form method=\"post\" action=\"bitter.cgi\" enctype=\"multipart/form-data\">
						Send a Bleat to make your friends feel bitter!
						<textarea name=\"send_bleat\" rows=\"1\" cols=\"60\"></textarea>
						<input type=\"file\" name=\"attachment\"  />
						<input type=\"submit\" name=\"send_bleat\" value=\"Send\" />
						<input type=\"hidden\" name=\"username\" value=\"$username\" />
						</form>";
				}

				if (scalar(@temp_result) == 0)
				{
					push @temp_result, "\nNo bleats from user: $username\n";
				}
				$temp = join '', @temp_result;
				$display_bleat = "${display_bleat}<div class=\"bitter_bleat_details\">$temp</div>";
				$display_bleat = "${display_bleat}<div class=\"bitter_heading\">Bleats with \@$username \/ Bleats from listens:</div>";

				%bleat_all = {};
				my @bleats = sort(glob("$bleats_dir/*")); # array of all bleats files
				my @bleat_result = ();
				my $filename;
				foreach my $b_file (@bleats) # loop in all bleat files, read bleats with @user or from listens
				{
					$filename = $b_file;
					$filename =~ s/.+\/bleats\///;
					$filename =~ s/ +//;
					chomp($filename);
					my $duplicate = 0;
					#my %b_map = map { $_ => 1 } @user_bleat_file_list;
					#if (exists($b_map{$filename})) # QUESTION NOT WORK!!!!!
					#if ($filename ~~ @user_bleat_file_list) # QUESTION NOT WORK!!!!!
					foreach my $b_name (@user_bleat_file_list) # if the bleat file already checked
					{
						if ($b_name == $filename)
						{
							$duplicate = 1;
							last;
						}
					}
					if ($duplicate)
					{
						next;
					}
					else # open the bleat file, check the lines
					{
						open my $B, "$b_file" or die "can not open $b_file: $!";
						my @lines = <$B>;
						my $time_of_bleat;
						my $tag_user = 0;
						my @temp_lines = ();
						my $tag;
						my $sender_name;
						for (@lines) # loop in one file, search content which from listens and @user
						{
							if ($_ =~ /latitude:/i)
							{
								next;
							}
							elsif ($_ =~ /longitude:/i)
							{
								next;
							}
							elsif ($_ =~ /in_reply_to:/i)
							{
								next;
							}
							elsif ($_ =~ /##[0-9]+##/) # has attachment
							{
								$tag = $_;
								$tag =~ s/\#+//g;
								next;
							}
							else
							{
								my $line = $_;
								if ($line =~ /\@/ && !$tag_user)
								{
									my $bleat = $line;
									chomp($bleat);
									$bleat =~ s/ +/ /;
									my @line_list = split ' ', $bleat;
									foreach my $word (@line_list)
									{
										if ($word =~ /\@/)
										{
											my $name = $word;
											$name =~ s/ +//g;
											$name =~ s/\@//;
											#if ($name == $username) # QUESTION! ALWAYS TRUE
											if ($name =~ /^$username$/i)
											{
												$tag_user = 1;
											}
											last;
										}
									}
								}
								if ($line =~ /username:/i)
								{
									$sender_name = $line;
									chomp($sender_name);
									$sender_name =~ s/username://;
									$sender_name =~ s/ +//g;
									if ($sender_name ~~ @my_listens) # the sender is in listen list
									{
										$tag_user = 1;
									}
								}
								if ($line =~ /time:/i)
								{
									$time_of_bleat = $line;
									$time_of_bleat =~ s/ *time: *//ig;
									$time_of_bleat =~ s/ +$//g;
									chomp($time_of_bleat);
								}
								if ($line =~ /bleat:/i)
								{
									chomp($line);
									$line =~ s/bleat: +//;
									if (!$suspend)
									{
										$line = "<a href=\"bitter.cgi?click_bleat=$filename&login_name=$username\">$line</a>\n";
									}
									else
									{
										$line = "$line\n";
									}
								}
								push @temp_lines, $line;
							}
						}
						if ($tag_user) # if the bleat contains the listens or mark of the user, record the time and the content
						{
							if ($tag)
							{
								if (-e "$users_dir/$sender_name/attachment/$tag.jpg") # the listen is not suspended
								{
									my $image = "$users_dir/$sender_name/attachment/$tag.jpg";
									push @temp_lines, "<img src=\"$image\" style=\"width:256px;height:256px;\">\n";
								}
								else # the listen is suspended
								{
									my $image = "$suspend_dir/$sender_name/attachment/$tag.jpg";
									push @temp_lines, "<img src=\"$image\" style=\"width:256px;height:256px;\">\n";
								}
							}
							push @temp_lines, "#";
							my $bleat_content = join '', @temp_lines;
							$bleat_all{$time_of_bleat} = $bleat_content
						}
					}
				}
				@temp_result = ();
				foreach my $time (reverse sort keys %bleat_all)
				{
					push @temp_result, "\n$bleat_all{$time}";
				}
				if (scalar(@temp_result) == 1)
				{
					push @temp_result, "No blreats with \@$username or from listens\n";
				}
				$temp = join '', @temp_result;
				$display_bleat = "${display_bleat}<div class=\"bitter_bleat_details\">$temp</div>";

				if (!$suspend) # if not suspend, display everything
				{
					print start_form, "\n";
					print submit('logout' => Logout), "\n";
					print end_form, "\n";
					print start_form, "\n";
					print "Search user:\n", textfield('search'), "\n";
					print submit(search => Search), "\n";
					print hidden(username => "$username"), "\n";
					print end_form, "\n";
					print start_form, "\n";
					print "Add listen:\n", textfield('add_listen'), "\n";
					print submit(add_listen => 'Add Listen'), "\n";
					print "Remove listen:\n", textfield('rm_listen'), "\n";
					print submit(rm_listen => 'Remove Listen'), "\n";
					print hidden(username => "$username"), "\n";
					print end_form, "\n";
					print start_form, "\n";
					print "Search Bleat:\n", textfield('search_bleat'), "\n";
					print submit(search_bleat => 'Search Bleat'), "\n";
					print hidden(username => "$username"), "\n";
					print end_form, "\n";
				}
				else # if suspended, only display logout and activate account
				{
					print start_form, "\n";
					print submit('logout' => Logout), "\n";
					print end_form, "\n";
					print start_form, "\n";
					print submit('activate_account' => 'Activate Account'), "\n";
					print hidden(username => "$username"), "\n";
					print end_form, "\n";
				}
			}
			else # wrong password
			{
				$display = "Wrong password\n";
				print start_form, "\n";
				print "Username:\n", textfield('username'), "\n";
				print "Password:\n", textfield('password'), "\n";
				print hidden(username => "$username"), "\n";
				print submit(value => Login), "\n";
				print "<a href=\"bitter.cgi?recover_account=
					1\"> Forgot your password?</a>";
				print end_form, "\n";
				print start_form, "\n";
				print "No account? Why not<a href=\"bitter.cgi?create_account=
					1\"> create an account</a> now, making your friends know you're a Bitter guy!";
				print end_form, "\n";
			}
		}
	}
	elsif (defined param("logout")) # Logout pressed
	{
		$username = ''; # empty all the variables QUESTION
		$password = '';
		$search = '';
		$send_bleat = '';
		$display = "<div class=\"bitter_heading\">Thanks for using bitter, wish you have a bitter day!</div>";
		print start_form, "\n";
		print "Username:\n", textfield('username'), "\n";
		print "Password:\n", textfield('password'), "\n";
		print submit(value => Login), "\n";
		print end_form, "\n";
	}
	elsif ((!$username || !$password) && !defined param("logout") && !$send_bleat && !$search && !param('click_username') 
		&& !$add_listen && !$rm_listen && !$search_bleat && !param('click_bleat') && !$reply_bleat && !param('create_account')
		&& !$create_profile && !param('recover_account') && !param('manage_image') && !param('manage_account') && !param('delete_bleat')
		&& !param('back') && !param('avatar') && !param('background') && !param('delete_avatar') && !param('delete_background')
		&& !param('activate_account') && !param('suspend_account') && !param('delete_account')) # when password or unername is empty, then display the whole login page again
	{
		print start_form, "\n";
		print "Username:\n", textfield('username'), "\n";
		print "Password:\n", textfield('password'), "\n";
		print submit(value => Login), "\n";
		print "<a href=\"bitter.cgi?recover_account=
			1\"> Forgot your password?</a>";
		print end_form, "\n";
		print start_form, "\n";
		print "No account? Why not<a href=\"bitter.cgi?create_account=
			1\"> create an account</a> now, making your friends know you're a Bitter guy!";
		print end_form, "\n";
	}

	if ($search) # search button pressed, search user
	{
		print start_form, "\n";
		print submit('logout' => Logout), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print submit(back => Back), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print "Add listen:\n", textfield('add_listen'), "\n";
		print submit(add_listen => 'Add Listen'), "\n";
		print "Remove listen:\n", textfield('rm_listen'), "\n";
		print submit(rm_listen => 'Remove Listen'), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print "Search user:\n", textfield('search'), "\n";
		print submit(search => Search), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print "Search Bleat:\n", textfield('search_bleat'), "\n";
		print submit(search_bleat => 'Search Bleat'), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";

		my $pattern = $search;
		my @users = sort(glob("$users_dir/*")); # array of usernames
		my @username_result = ();
		my @realname_result = ();
		for my $username_path (@users) # loop in usernames
		{
			my $username_from_path = $username_path;
			$username_from_path =~ s/.*\///;
			if ($username_from_path =~ /$pattern/i && !($username_from_path =~ /$username/i)) # if the searched content is in the file path, which means in username, and cannot be myself
			{
				my $user_detail_file = "$username_path/details.txt";
				my $result;
				open my $U, "$user_detail_file" or die "can not open $user_detail_file: $!";
				my @user_content = <$U>;
				for (@user_content)
				{
					if ($_ =~ /full_name/i)
					{
						$result = $_;
						$result =~ s/ *full_name: *//ig;
						$result =~ s/ +$//g;
						chomp($result);
						push @realname_result, $result;
					}
					elsif ($_ =~ /username/i)
					{
						$result = $_;
						$result =~ s/ *username: *//ig;
						$result =~ s/ +$//g;
						chomp($pwd);
						push @username_result, $result;
					}
				}
			}
		}
		my $size = @username_result;
		my @result = [];
		$result[0] = "Search result of username & real name (please click username for more information):\n";
		if ($size == 0)
		{
			my $str = "No search result\n";
			push @result, $str;
		}
		else
		{
			for (my $i = 0; $i < $size; $i ++)
			{	
				if (!$realname_result[$i])
				{
					$realname_result[$i] = "(no real name info)";
				}
				my $str = "username: <a href=\"bitter.cgi?click_username=
					$username_result[$i]&login_name=$username\">$username_result[$i]</a>real name: $realname_result[$i]\n";
				push @result, $str;
			}
		}
		$display = "<div class=\"bitter_heading\">User login as: $username</div>";
		my $temp = join "\n", @result;
		$display = "$display$temp";
	}

	if (param('click_username')) # the username in the search result is clicked
	{
		print start_form, "\n";
		print submit('logout' => Logout), "\n";
		print end_form, "\n";

		my $username = param('login_name');
		my $name = param('click_username');
		my @users = sort(glob("$users_dir/*")); # array of usernames
		my @user_content;
		my @display_content;
		my %bleat_all;
		print start_form, "\n";
		print submit(back => Back), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";

		print start_form, "\n";
		print "Add listen:\n", textfield('add_listen'), "\n";
		print submit(add_listen => 'Add Listen'), "\n";
		print "Remove listen:\n", textfield('rm_listen'), "\n";
		print submit(rm_listen => 'Remove Listen'), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";

		for my $username_path (@users)
		{
			if ($username_path =~ /$name/i) # if the file path contains the username
			{
				#
				# part of displaying user infomation
				#
				my $user_detail_file = "$username_path/details.txt";
				my $user_bleat_file = "$username_path/bleats.txt";
				my $user_image = "$username_path/profile.jpg";
				open my $U, "$user_detail_file" or die "can not open $user_detail_file: $!";
				@user_content = <$U>;
				for (@user_content)
				{
					if ($_ =~ /password:/i)
					{
						next;
					}
					elsif ($_ =~ /email:/i)
					{
						next;
					}
					else
					{
						push @display_content, $_;
					}
				}
				my $image = '';
				if (-e $user_image)
				{
					$image = "<img src=\"$user_image\" style=\"width:256px;height:256px;\">\n"
				}
				else
				{
					$image = "(no user avatar)\n";
				}
				$display = "<div class=\"bitter_heading\">User login as: $username</div>$image";
				my $temp = join "", @display_content;
				$display = "$display$temp";

				#
				# part of displaying bleats from the user
				#
				open my $B, "$user_bleat_file" or die "can not open $user_bleat_file: $!"; # read the content of user bleat index file
				my @user_bleat_file_list = <$B>;
				for (@user_bleat_file_list)
				{
					my $filename = $_;
					my $time_of_bleat;
					my $file_of_bleat = "$bleats_dir/$_";
					open my $F, "$file_of_bleat" or die "can not open $file_of_bleat: $!";
					my @lines = <$F>;
					my @temp_lines = ();
					my $tag;
					for (@lines)
					{
						if ($_ =~ /latitude:/i)
						{
							next;
						}
						elsif ($_ =~ /longitude:/i)
						{
							next;
						}
						elsif ($_ =~ /in_reply_to:/i)
						{
							next;
						}
						elsif ($_ =~ /username:/i)
						{
							next;
						}
						elsif ($_ =~ /##[0-9]+##/) # has attachment
						{
							$tag = $_;
							$tag =~ s/\#+//g;
							next;
						}
						else
						{
							my $line = $_;
							if ($line =~ /time:/i)
							{
								$time_of_bleat = $line;
								$time_of_bleat =~ s/ *time: *//ig;
								$time_of_bleat =~ s/ +$//g;
								chomp($time_of_bleat);
							}
							if ($line =~ /bleat:/i)
							{
								chomp($line);
								$line =~ s/bleat: +//;
								$line = "<a href=\"bitter.cgi?click_bleat=
									$filename&login_name=$username\">$line</a>\n";
							}
							push @temp_lines, $line;
						}
					}
					if ($tag)
					{
						my $image = "$users_dir/$name/attachment/$tag.jpg";
						push @temp_lines, "<img src=\"$image\" style=\"width:256px;height:256px;\">\n";
					}
					push @temp_lines, "#";
					my $bleat_content = join '', @temp_lines;
					$bleat_all{$time_of_bleat} = $bleat_content;
				}
				my @temp_result;
				foreach my $time (reverse sort keys %bleat_all)
				{
					push @temp_result, "\n$bleat_all{$time}";
				}
				if (scalar(@temp_result) == 0)
				{
					push @temp_result, "\nNo bleats from user: $name\n";
				}
				$temp = join '', @temp_result;
				$display_bleat = "<div class=\"bitter_heading\">Bleats from user: $name</div>";
				$display_bleat = "${display_bleat}<div class=\"bitter_bleat_details\">$temp</div>";
				last;
			}
		}
	}

	if ($send_bleat) # send bleats pressed, only display after a user login in
	{
		#print hidden(username => "$username"), "\n";
		print start_form, "\n";
		print submit('logout' => Logout), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print submit(back => Back), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";
		$display = "<div class=\"bitter_heading\">User login as: $username</div>";

		my $user = glob("$users_dir/$username"); # path of the specific username
		my $user_detail_file = "$user/details.txt";
		my $user_bleat_file = "$user/bleats.txt";

		my $bleat = $send_bleat;
		my $base_value = 2041900000; # the bleat number is generate randomly
		my $random_index = int(rand(65535));
		my $random_attachment = int(rand(100));
		my $destination_file;
		my @all_attachment;
		my $tag;

		if (length($bleat) > 142)
		{
			$display = "${display}Bleat is too long (limitation is 142 characters), you cannot make your friends feel bitter with such a long Bleat!\n";
		}
		else
		{
			if (param('attachment')) # uploading attachment of a bleat
			{
				if (!(-e "$user/attachment"))
				{
					mkdir "$user/attachment" or die "Unable to create $user/attachment: $!";
				}
				@all_attachment = sort(glob("$user/attachment/*"));
				if (scalar(@all_attachment) == 4)
				{
					$display = "${display}Attachment uploading failed, your maximum allowed number of attachments is 4\n";
				}
				else
				{
					$destination_file = "$user/attachment/${random_attachment}.jpg";
					my $query = new CGI; # write the image to destination file, in binmode, this will cover the original avatar/background (if it exists)
					my $upload_filehandle = $query->upload('attachment');
					while (1)
					{
						if (-e $destination_file)
						{
							$random_attachment = int(rand(100));
							$destination_file = "$user/attachment/${random_attachment}.jpg";
						}
						else
						{
							last;
						}
					}
					open my $IMAGE,">$destination_file";
					binmode $IMAGE;
					while (my $line = <$upload_filehandle>)
					{
						print $IMAGE $line;
					}
					close $IMAGE;
					$tag = 1;
				}
			}

			my $bleat_number;
			my $bleat_file;
			while (1)
			{
				my $result = $base_value + $random_index;
				$bleat_number = "$result";
				$bleat_file = "$bleats_dir/$bleat_number"; # bleat file path
				if (-e $bleat_file) # if the bleat number is already used, then generate another bleat number
				{
					$random_index = int(rand(65535));
				}
				else
				{
					last;
				}
			}
			my $timestamp = time();
			open(my $B1, '>', $bleat_file) or die "can not create $bleat_file: $!"; # write the bleat file (overwrite)
			print $B1 "username: $username\n";
			print $B1 "time: $timestamp\n";
			print $B1 "bleat: $bleat";
			if ($tag)
			{
				print $B1 "\n##${random_attachment}##";
			}
			close $B1;
			open(my $B2, '>>', $user_bleat_file) or die "can not open $user_bleat_file: $!"; # write the user bleat number file (append)
			print $B2 "$bleat_number\n";
			close $B2;

			my $mark;
			if ($bleat =~ /\@/) # if the bleat marks a user, then make a copy to notification folder
			{
				chomp($bleat);
				$bleat =~ s/ +/ /;
				my @line_list = split ' ', $bleat;
				foreach my $word (@line_list)
				{
					if ($word =~ /\@/)
					{
						$mark = $word;
						$mark =~ s/ +//g;
						$mark =~ s/\@//;
						last;
					}
				}
				if (!(-e "$notification_dir/$mark"))
				{
					if (!(-e "$notification_dir"))
					{
						mkdir "$notification_dir" or die "Failed in creating directory $notification_dir: $!";
					}
					mkdir "$notification_dir/$mark" or die "Failed in creating directory $notification_dir/$mark: $!";
				}
				my $copy = "$notification_dir/$mark/$bleat_number";
				open(my $B, '>', $copy) or die "can not create $copy: $!"; # write the bleat file (overwrite)
				print $B "username: $username\n";
				print $B "bleat: $content\n";
				close $B;
			}

			$display = "${display}Bleat sent:\n\nBleat ID: $bleat_number\nTime: $timestamp\nBleat content: $bleat\n";
			if ($tag)
			{
				$display = "${display}Attachment:\n<img src=\"$destination_file\" style=\"width:256px;height:256px;\">\n";
			}
		}
	}

	if ($add_listen) # add listen button is pressed
	{
		print start_form, "\n";
		print submit('logout' => Logout), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print submit(back => Back), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";

		$display = "<div class=\"bitter_heading\">User login as: $username</div>";
		my $new_username = $add_listen;
		$new_username =~ s/ +//g;
		my @users = sort(glob("$users_dir/*")); # array of usernames
		my @suspends = sort(glob("$suspend_dir/*"));
		my $user = glob("$users_dir/$username"); # path of the specific username
		my $user_detail_file = "$user/details.txt"; # dataset-small/users/xxxxx/details.txt
		my $username_result = 0;
		my @my_listens;
		for my $username_path (@users)
		{
			if ($username_path =~ /$new_username/i) # if the searched content is in the file path, which means in username
			{
				$username_result = 1;
				last;
			}
		}
		for my $username_path (@suspends)
		{
			if ($username_path =~ /$del_username/i) # if the searched content is in the file path, which means in username
			{
				$username_result = 1;
				last;
			}
		}
		if (!$username_result) # no such username
		{
			$display = "${display}No user named \"$new_username\"";
		}
		else # get the username, add to user detail.txt file
		{
			open my $IN, "<$user_detail_file" or die "can not open $user_detail_file: $!";
			my @original_content = <$IN>;
			for (@original_content) # get the listens
			{
				if ($_ =~ /listens:/i)
				{
					my $listen = $_;
					chomp($listen);
					$listen =~ s/ *listens: *//i;
					$listen =~ s/ +/ /g;
					@my_listens = split / /, $listen;
					last;
				}
			}
			close $IN;
			if ($new_username ~~ @my_listens) # username already in list
			{
				$display = "${display}User: $new_username is already under listerning";
			}
			else # username is not in the list, add it to list
			{
				open my $OUT, ">$user_detail_file" or die "can not write $user_detail_file: $!";
				foreach my $line (@original_content)
				{
					if (!($line =~ /listens:/i))
					{
						print $OUT $line;
					}
					else
					{
						chomp($line);
						my $newline = "$line $new_username\n";
						print $OUT $newline;
						push @my_listens, $new_username;
					}
				}
				close $OUT;
			}
			$display = "${display}\nCurrent listens: ";
			if (scalar(@my_listens) < 1)
			{
				push @my_listens, "(no listens)";
			}
			foreach my $listen (@my_listens)
			{
				$display = "${display}$listen / ";
			}
			$display = "${display}\n";
		}
	}

	if ($rm_listen)
	{
		print start_form, "\n";
		print submit('logout' => Logout), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print submit(back => Back), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";

		$display = "<div class=\"bitter_heading\">User login as: $username</div>";
		my $del_username = $rm_listen;
		$del_username =~ s/ +//g;
		my @users = sort(glob("$users_dir/*")); # array of usernames
		my @suspends = sort(glob("$suspend_dir/*"));
		my $user = glob("$users_dir/$username"); # path of the specific username
		my $user_detail_file = "$user/details.txt"; # dataset-small/users/xxxxx/details.txt
		my $username_result = 0;
		my @my_listens;
		for my $username_path (@users)
		{
			if ($username_path =~ /$del_username/i) # if the searched content is in the file path, which means in username
			{
				$username_result = 1;
				last;
			}
		}
		for my $username_path (@suspends)
		{
			if ($username_path =~ /$del_username/i) # if the searched content is in the file path, which means in username
			{
				$username_result = 1;
				last;
			}
		}
		if (!$username_result) # no such username
		{
			$display = "${display}No user named \"$del_username\"";
		}
		else # get the username, delete it from detail.txt file
		{
			open my $IN, "<$user_detail_file" or die "can not open $user_detail_file: $!";
			my @original_content = <$IN>;
			for (@original_content)
			{
				if ($_ =~ /listens:/i)
				{
					my $listen = $_;
					chomp($listen);
					$listen =~ s/ *listens: *//i;
					$listen =~ s/ +/ /g;
					@my_listens = split / /, $listen;
					last;
				}
			}
			close $IN;
			if (!($del_username ~~ @my_listens)) # username is not in list
			{
				$display = "${display}You are not listerning user: $del_username";
			}
			else # username is in the list, remove it
			{
				open my $OUT, ">$user_detail_file" or die "can not write $user_detail_file: $!";
				foreach my $line (@original_content)
				{
					if (!($line =~ /listens:/i))
					{
						print $OUT $line;
					}
					else
					{
						chomp($line);
						my $newline = $line;
						$newline =~ s/ $del_username//;
						$newline = "$newline\n";
						print $OUT $newline;
					}
				}
				close $OUT;
			}
			$display = "${display}\nCurrent listens: ";
			if (scalar(@my_listens) < 1)
			{
				push @my_listens, "(no listens)";
			}
			foreach my $listen (@my_listens) # display the result
			{
				if (!($listen =~ /^$del_username$/))
				{
					$display = "${display}$listen / ";
				}
			}
			$display = "${display}\n";
		}
	}

	if ($search_bleat) # search bleat button is pressed
	{
		print start_form, "\n";
		print submit('logout' => Logout), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print submit(back => Back), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print "Add listen:\n", textfield('add_listen'), "\n";
		print submit(add_listen => 'Add Listen'), "\n";
		print "Remove listen:\n", textfield('rm_listen'), "\n";
		print submit(rm_listen => 'Remove Listen'), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print "Search user:\n", textfield('search'), "\n";
		print submit(search => Search), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print "Search Bleat:\n", textfield('search_bleat'), "\n";
		print submit(search_bleat => 'Search Bleat'), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";

		$display = "<div class=\"bitter_heading\">User login as: $username</div>";
		my $pattern = $search_bleat;
		my @bleats = sort(glob("$bleats_dir/*")); # array of all bleats files
		my @bleat_result = ();
		$display_bleat = "<div class=\"bitter_heading\">Search Result of Bleats</div>";
		my %bleat_all;
		foreach my $b_file (@bleats) # loop in all bleat files
		{
			my $filename = $b_file;
			$filename =~ s/.+\/bleats\///;
			open my $B, "$b_file" or die "can not open $b_file: $!";
			my @bleat_content = <$B>;
			my $find_tag = 0;
			my @temp_lines = ();
			my $time_of_bleat;
			my $name;
			my $tag;
			for (@bleat_content) # loop in one file
			{
				if ($_ =~ /latitude:/i)
				{
					next;
				}
				elsif ($_ =~ /longitude:/i)
				{
					next;
				}
				elsif ($_ =~ /in_reply_to:/i)
				{
					next;
				}
				elsif ($_ =~ /##[0-9]+##/) # has attachment
				{
					$tag = $_;
					$tag =~ s/\#+//g;
					next;
				}
				else
				{
					my $line = $_;
					if ($line =~ /bleat:/i || $line =~ /#.+/) # if it is the line of bleat or has # sign
					{
						if ($line =~ /$pattern/i) # bleat contains the pattern
						{
							$find_tag = 1;
						}
					}
					if ($line =~ /time:/i)
					{
						$time_of_bleat = $line;
						$time_of_bleat =~ s/ *time: *//ig;
						$time_of_bleat =~ s/ +$//g;
						chomp($time_of_bleat);
					}
					if ($line =~ /bleat:/i)
					{
						chomp($line);
						$line =~ s/bleat: +//;
						$line = "<a href=\"bitter.cgi?click_bleat=
							$filename&login_name=$username\">$line</a>\n";
					}
					if ($line =~ /username:/i)
					{
						$name = $line;
						chomp($name);
						$name =~ s/username://;
						$name =~ s/ +//g;
					}
					push @temp_lines, $line;
				}
			}
			if ($find_tag) # find the bleat, push into hash table
			{
				if ($tag)
				{
					my $image = "$users_dir/$name/attachment/$tag.jpg";
					push @temp_lines, "<img src=\"$image\" style=\"width:256px;height:256px;\">\n";
				}
				push @temp_lines, "#";
				my $bleat_content = join '', @temp_lines;
				$bleat_all{$time_of_bleat} = $bleat_content;
			}
		}
		foreach my $time (reverse sort keys %bleat_all)
		{
			push @bleat_result, "\n$bleat_all{$time}";
		}
		if (scalar(@bleat_result) == 0)
		{
			push @bleat_result, "\nNo bleats with searched pattern: $pattern\n";
		}
		my $temp = join '', @bleat_result;
		$display_bleat = "${display_bleat}<div class=\"bitter_bleat_details\">$temp</div>";
	}

	if (param('click_bleat')) # the bleat is clicked for replying and viewing any bleats which reply to it
	{
		print start_form, "\n";
		print submit('logout' => Logout), "\n";
		print end_form, "\n";

		$username = param('login_name');
		$checked_bleat = param('click_bleat');
		print start_form, "\n";
		print submit(back => Back), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";

		$display = "<form method=\"post\" action=\"bitter.cgi\" enctype=\"multipart/form-data\">
			Reply to bleat $checked_bleat:
			<textarea name=\"reply_bleat\" rows=\"3\" cols=\"60\"></textarea>
			<input type=\"file\" name=\"attachment\" />
			<input type=\"submit\" name=\"reply_bleat\" value=\"Reply\" />
			<input type=\"hidden\" name=\"username\" value=\"$username\" />
			<input type=\"hidden\" name=\"checked_bleat\" value=\"$checked_bleat\" />
			</form>";
		$display = "${display}<div class=\"bitter_heading\">User login as: $username</div>Please input text above for replying to bleat: $checked_bleat\n\n";
		my $checked_bleat_file = "$bleats_dir/$checked_bleat";
		open my $B, "$checked_bleat_file" or die "can not open $checked_bleat_file: $!";
		my @checked_bleat_content = <$B>;
		my $tag;
		my $name;
		if (param('notification')) # if the bleat is notification, remove the copy file
		{
			if (-e "$notification_dir/$username/$checked_bleat")
			{
				unlink "$notification_dir/$username/$checked_bleat";
			}
		}
		for (@checked_bleat_content) # display the clicked bleat's content and source (from who)
		{
			if ($_ =~ /bleat:/i)
			{
				chomp($_);
				$_ =~ s/bleat: +//;
				$display = "${display}Bleat content: $_\n";
			}
			if ($_ =~ /username:/i)
			{
				$name = $_;
				chomp($name);
				$name =~ s/username: +//;
				$display = "${display}From user: $name\n";
			}
			if ($_ =~ /##[0-9]+##/) # has attachment
			{
				$tag = $_;
				$tag =~ s/\#+//g;
				next;
			}
		}
		if ($tag)
		{
			if (-e "$users_dir/$name/attachment/$tag.jpg")
			{
				my $image = "$users_dir/$name/attachment/$tag.jpg";
				$display = "${display}Attachment:\n<img src=\"$image\" style=\"width:256px;height:256px;\">\n";
			}
			else
			{
				my $image = "$suspend_dir/$name/attachment/$tag.jpg";
				$display = "${display}Attachment:\n<img src=\"$image\" style=\"width:256px;height:256px;\">\n";
			}
		}

		my @bleats = sort(glob("$bleats_dir/*")); # array of all bleats files
		my @bleat_result = ();
		my %bleat_all;
		foreach my $b_file (@bleats) # loop in all bleat files, searching bleats which respond to the clicked bleat
		{
			my $filename = $b_file;
			$filename =~ s/.+\/bleats\///;
			open my $B, "$b_file" or die "can not open $b_file: $!";
			my @bleat_content = <$B>;
			my $find_tag = 0;
			my @temp_lines = ();
			my $time_of_bleat;
			my $tag;
			my $name;
			for (@bleat_content) # loop in one file
			{
				my $line = $_;
				if ($_ =~ /latitude:/i)
				{
					next;
				}
				elsif ($_ =~ /longitude:/i)
				{
					next;
				}
				elsif ($_ =~ /##[0-9]+##/) # has attachment
				{
					$tag = $_;
					$tag =~ s/\#+//g;
					next;
				}
				elsif ($line =~ /in_reply_to:/i) # if it is the line of reply
				{
					$line =~ s/ +//g;
					$line =~ s/in_reply_to://;
					chomp($line);
					if ($line =~ /^$checked_bleat$/) # the bleat is find
					{
						$find_tag = 1;
					}
					next;
				}
				else
				{
					if ($line =~ /time:/i)
					{
						$time_of_bleat = $line;
						$time_of_bleat =~ s/ *time: *//ig;
						$time_of_bleat =~ s/ +$//g;
						chomp($time_of_bleat);
					}
					if ($line =~ /bleat:/i)
					{
						chomp($line);
						$line =~ s/bleat: +//;
						$line = "<a href=\"bitter.cgi?click_bleat=
							$filename&login_name=$username\">$line</a>\n";
					}
					if ($line =~ /username:/i)
					{
						$name = $line;
						chomp($name);
						$name =~ s/username://;
						$name =~ s/ +//g;
					}
					push @temp_lines, $line;
				}
			}
			if ($find_tag) # if find, push it to the hash table based on time
			{
				if ($tag)
				{
					if (-e "$users_dir/$name/attachment/$tag.jpg")
					{
						my $image = "$users_dir/$name/attachment/$tag.jpg";
						push @temp_lines, "<img src=\"$image\" style=\"width:256px;height:256px;\">\n";
					}
					else
					{
						my $image = "$suspend_dir/$name/attachment/$tag.jpg";
						push @temp_lines, "<img src=\"$image\" style=\"width:256px;height:256px;\">\n";
					}
				}
				push @temp_lines, "#";
				my $bleat_content = join '', @temp_lines;
				$bleat_all{$time_of_bleat} = $bleat_content;
			}
		}
		foreach my $time (reverse sort keys %bleat_all)
		{
			push @bleat_result, "\n$bleat_all{$time}";
		}
		if (scalar(@bleat_result) == 0)
		{
			push @bleat_result, "\nNo bleats respond to bleat $checked_bleat\n";
		}
		my $temp = join '', @bleat_result;
		$display_bleat = "<div class=\"bitter_heading\">Search result of bleats responding to bleat $checked_bleat</div>";
		$display_bleat = "${display_bleat}<div class=\"bitter_bleat_details\">$temp</div>";
	}

	if (param('delete_bleat')) # delete a bleat
	{
		print start_form, "\n";
		print submit('logout' => Logout), "\n";
		print end_form, "\n";

		$username = param('login_name');
		$delete_bleat = param('delete_bleat');
		$display = "<div class=\"bitter_heading\">User login as: $username</div>";
		my $user = glob("$users_dir/$username"); # path of the specific username
		my $user_bleat_file = "$user/bleats.txt";
		my $bleat = "$bleats_dir/$delete_bleat"; # path of the specific bleat file

		open my $U, "<$user_bleat_file" or die "can not open $user_bleat_file: $!";
		my @bleat_index = <$U>;
		close $U;
		open(my $B, '>', $user_bleat_file) or die "can not open $user_bleat_file: $!"; # remove the bleat from user bleat file
		foreach my $line (@bleat_index)
		{
			if (!($line =~ /$delete_bleat/))
			{
				print $B $line;
			}
		}
		close $B;

		open my $B, "<$bleat" or die "can not open $bleat: $!";
		my @bleat_content = <$B>;
		my $tag;
		for (@bleat_content) # search for attachment
		{
			if ($_ =~ /##[0-9]+##/) # has attachment
			{
				$tag = $_;
				$tag =~ s/\#+//g;
				last;
			}
		}
		close $B;
		unlink $bleat or die "Bleat $delete_bleat is already deleted"; # remove the real bleat file
		if ($tag)
		{
			unlink "$user/attachment/$tag.jpg" or die "Attachment $user/attachment/$tag.jpg is already deleted"; # remove the attachment
		}
		$display = "${display}Bleat $delete_bleat from user $username has been deleted successfully\n";
		print start_form, "\n";
		print submit(back => Back), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";
	}

	if ($reply_bleat) # reply bleat button is clicked
	{
		print start_form, "\n";
		print submit('logout' => Logout), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print submit(back => Back), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";

		$display = "<div class=\"bitter_heading\">User login as: $username</div>";
		my $content = $reply_bleat;
		my $base_value = 2041900000;
		my $random_index = int(rand(65535));
		my $user = glob("$users_dir/$username"); # path of the specific username
		my $user_bleat_file = "$user/bleats.txt";
		my $random_attachment = int(rand(100));
		my $destination_file;
		my @all_attachment;
		my $tag = 0;

		if (length($content) > 142) # if the bleat is too long (over 142 characters)
		{
			$display = "${display}Bleat is too long (limitation is 142 characters), you cannot make your friends feel bitter with such a long Bleat!\n";
		}
		else
		{
			if (param('attachment')) # uploading attachment of a bleat
			{
				if (!(-e "$user/attachment"))
				{
					mkdir "$user/attachment" or die "Unable to create $user/attachment: $!";
				}
				@all_attachment = sort(glob("$user/attachment/*"));
				if (scalar(@all_attachment) == 4)
				{
					$display = "${display}Attachment uploading failed, your reached your maximum number of attachments (4)\n";
				}
				else
				{
					$destination_file = "$user/attachment/${random_attachment}.jpg";
					my $query = new CGI; # write the image to destination file, in binmode, this will cover the original avatar/background (if it exists)
					my $upload_filehandle = $query->upload('attachment');
					while (1)
					{
						if (-e $destination_file)
						{
							$random_attachment = int(rand(100));
							$destination_file = "$user/attachment/${random_attachment}.jpg";
						}
						else
						{
							last;
						}
					}
					open my $IMAGE,">$destination_file";
					binmode $IMAGE;
					while (my $line = <$upload_filehandle>)
					{
						print $IMAGE $line;
					}
					close $IMAGE;
					$tag = 1;
				}
			}

			my $bleat_file;
			my $bleat_number;
			while (1)
			{
				my $result = $base_value + $random_index;
				$bleat_number = "$result";
				$bleat_file = "$bleats_dir/$bleat_number"; # bleat file path
				if (-e $bleat_file) # check whether the bleat number is already existed
				{
					$random_index = int(rand(65535));
				}
				else
				{
					last;
				}
			}
			my $timestamp = time();
			chomp($content);
			open(my $B1, '>', $bleat_file) or die "can not create $bleat_file: $!"; # write the new bleat file
			print $B1 "username: $username\n";
			print $B1 "time: $timestamp\n";
			print $B1 "bleat: $content\n";
			print $B1 "in_reply_to: $checked_bleat";
			if ($tag)
			{
				print $B1 "\n##${random_attachment}##";
			}
			close $B1;
			open(my $B2, '>>', $user_bleat_file) or die "can not open $user_bleat_file: $!"; # append new bleat number to user bleat index file
			print $B2 "$bleat_number\n";
			close $B2;

			$display = "${display}Bleat replied to $checked_bleat:\n\nBleat ID: $bleat_number\nTime: $timestamp\nBleat content: $content\n";
			if ($tag)
			{
				$display = "${display}Attachment:\n<img src=\"$destination_file\" style=\"width:256px;height:256px;\">\n";
			}

			my $mark;
			open my $U, "$bleats_dir/$checked_bleat" or die "can not open $bleats_dir/$checked_bleat: $!";
			my @replied_content = <$U>;
			for (@replied_content) # if the bleat marks a user, then make a copy to notification folder
			{
				if ($_ =~ /username:/)
				{
					$mark = $_;
					chomp($mark);
					$mark =~ s/username: +//;
					last;
				}
			}
			if (!(-e "$notification_dir/$mark"))
			{
				if (!(-e "$notification_dir"))
				{
					mkdir "$notification_dir" or die "Failed in creating directory $notification_dir: $!";
				}
				mkdir "$notification_dir/$mark" or die "Failed in creating directory $notification_dir/$mark: $!";
			}
			my $copy = "$notification_dir/$mark/$bleat_number";
			open(my $B, '>', $copy) or die "can not create $copy: $!"; # write the bleat file (overwrite)
			print $B "username: $username\n";
			print $B "time: $timestamp\n";
			print $B "bleat: $content\n";
			close $B;
		}
	}

	if (param('create_account') && (!$create_username || !$create_password || !$create_email) && !param('confirm_account')) # display screen for creating a new account
	{
		print start_form, "\n";
		print "New Username:\n", textfield('create_username'), "\n";
		print "New Password:\n", textfield('create_password'), "\n";
		print "New Email:\n", textfield('create_email'), "\n";
		print hidden(create_account => "$create_account"), "\n";
		print submit(value => Create), "\n";
		print end_form, "\n";
		$display = "<div class=\"bitter_heading\">You are creating your new Bitter account</div>";
	}

	if (param('create_account') && $create_username && $create_password && $create_email && !param('confirm_account')) # process creating a new account
	{
		my $c_username = $create_username;
		my $c_password = $create_password;
		my $c_email = $create_email;
		my @users = sort(glob("$users_dir/*")); # array of usernames
		$display = "<div class=\"bitter_heading\">You are creating your new Bitter account</div>";
		my $good_username = 1;

		if ($c_username =~ /\#|\$|\.|\@|\%|\^|\&|\*|\~|\`|\ /) # invalid characters in username
		{
			print start_form, "\n";
			print "New Username:\n", textfield('create_username'), "\n";
			print "New Password:\n", textfield('create_password'), "\n";
			print "New Email:\n", textfield('create_email'), "\n";
			print hidden(create_account => "$create_account"), "\n";
			print submit(value => Login), "\n";
			print end_form, "\n";
			$display = "${display}Error:\nUsername contains invalid characters";
		}
		elsif (length($c_password) < 6) # password is too short
		{
			print start_form, "\n";
			print "New Username:\n", textfield('create_username'), "\n";
			print "New Password:\n", textfield('create_password'), "\n";
			print "New Email:\n", textfield('create_email'), "\n";
			print hidden(create_account => "$create_account"), "\n";
			print submit(value => Login), "\n";
			print end_form, "\n";
			$display = "${display}Error:\nPassword too short, it should be longer than 6 characters";
		}
		elsif (!($c_email =~ /^[^ \@\#\$\%\^\&\*]+\@[^ \@\#\$\%\^\&\*]+\.[a-zA-Z]+$/) || $c_email =~ /unsw/i) # email is from unsw or an invalid format
		{
			print start_form, "\n";
			print "New Username:\n", textfield('create_username'), "\n";
			print "New Password:\n", textfield('create_password'), "\n";
			print "New Email:\n", textfield('create_email'), "\n";
			print hidden(create_account => "$create_account"), "\n";
			print submit(value => Login), "\n";
			print end_form, "\n";
			$display = "${display}Error:\nAn invalid email format";
		}
		else # everything is fine
		{
			for (@users) #check the existence of username
			{
				my $current_name = $_;
				$current_name =~ s/.+\/users\///;
				chomp($current_name);
				#if ($c_username == $current_name) # QUESTION!!!!! NOT WORK!!!
				if ($c_username =~ /^$current_name$/)
				{
					print start_form, "\n";
					print "New Username:\n", textfield('create_username'), "\n";
					print "New Password:\n", textfield('create_password'), "\n";
					print "New Email:\n", textfield('create_email'), "\n";
					print hidden(create_account => "$create_account"), "\n";
					print submit(value => Login), "\n";
					print end_form, "\n";
					$display = "${display}Error:\nThe new username is already used";
					$good_username = 0;
					last;
				}
			}

			if ($good_username) # sending email for confirmation
			{
				$to = "$c_email";
				$from = "chengjia.xu@student.unsw.edu.au";
				$subject = "A Bitter greeting!";
				$message = "Please click the link to finish the registration:\n$ENV{SCRIPT_URI}?create_account=1&confirm_account=1&c_name=$c_username&c_pwd=$c_password&c_add=$c_email";
				 
				open(MAIL, "|/usr/sbin/sendmail -t");
				print MAIL "To: $to\n";
				print MAIL "From: $from\n";
				print MAIL "Subject: $subject\n\n";
				print MAIL $message;

				$display = "${display}A very Bitter confirmation email has ben sent to your email address: $c_email\n";
			}
		}
	}

	if (param('create_account') && param('confirm_account')) # the confirmation email for account creating is clicked
	{
		my $c_username = param('c_name');
		my $c_password = param('c_pwd');
		my $c_email = param('c_add');
		my @users = sort(glob("$users_dir/*")); # array of usernames
		my $user_detail_file = "$users_dir/$c_username/details.txt";
		my $user_bleat_file = "$users_dir/$c_username/bleats.txt";

		if (!(-e "$users_dir/$c_username"))
		{
			mkdir "$users_dir/$c_username" or die "Unable to create $users_dir/$c_username: $!"; # create new user directory
			open my $OUT, ">$user_bleat_file" or die "can not write $user_bleat_file: $!"; # write new bleat.txt
			print $OUT '';
			close $OUT;
			open my $OUT, ">$user_detail_file" or die "can not write $user_detail_file: $!"; # write new user details.txt
			print $OUT "username: $c_username\n";
			print $OUT "password: $c_password\n";
			print $OUT "email: $c_email\n";
			print $OUT "listens: \n";
			print $OUT "home_longitude: \n";
			print $OUT "home_latitude: \n";
			print $OUT "home_suburb: ";
			close $OUT;

			$display = "<div class=\"bitter_heading\">Congratulation, now you are a Bitter guy, you are now much Bitter than all the others!</div>New username: $c_username\nBinded email: $c_email";
		}
		else # the username is already existed, an illegal operatin
		{
			$display = "<div class=\"bitter_heading\">Illegal operation!</div>";
		}
	}

	if ($create_profile) # create user profile.txt
	{
		print start_form, "\n";
		print submit('logout' => Logout), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print submit(back => Back), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";

		#$username = param('login_name');
		my $user = glob("$users_dir/$username"); # path of the specific username
		my $user_detail_file = "$user/details.txt"; # dataset-small/users/xxxxx/details.txt
		my $user_profile_file = "$user/profile.txt";
		open my $OUT, ">$user_profile_file" or die "can not write $user_profile_file: $!";
		print $OUT "$create_profile\n";
		close $OUT;

		$display = "<div class=\"bitter_heading\">User login as: $username</div>Your profile information has been created:\n$create_profile";
	}

	if (param('recover_account') && (!$original_username || !$original_email) && !param('confirm_recover') && !param('new_password')) # password recovery step 1, enter username and email
	{
		print start_form, "\n";
		print "Registered Username:\n", textfield('original_username'), "\n";
		print "Registered Email:\n", textfield('original_email'), "\n";
		print hidden(recover_account => "$recover_account"), "\n";
		print submit(value => Recover), "\n";
		print end_form, "\n";
		$display = "<div class=\"bitter_heading\">In password recovering</div>Please enter your registed username and email address\nBitter will send you a very Bitter email for password recovery/change\n";
	}

	if (param('recover_account') && $original_username && $original_email && !param('confirm_recover') && !param('new_password')) # password recovery step 2, sending email
	{
		my @users = sort(glob("$users_dir/*")); # array of usernames
		my $user_legal = 0;
		my $email_legal = 0;
		$display = "<div class=\"bitter_heading\">In password recovering</div>";
		for my $username_path (@users)
		{
			if ($username_path =~ /$original_username/i) # if the searched content is in the file path
			{
				$user_legal = 1;
				last;
			}
		}
		if (!$user_legal) # an illegal username
		{
			print start_form, "\n";
			print "Registered Username:\n", textfield('original_username'), "\n";
			print "Registered Email:\n", textfield('original_email'), "\n";
			print hidden(recover_account => "$recover_account"), "\n";
			print submit(value => Recover), "\n";
			print end_form, "\n";
			$display = "${display}Error:\nUsername is not valid";
		}
		else # an legal username
		{
			my $user_detail_file = "$users_dir/$original_username/details.txt";
			open my $U, "$user_detail_file" or die "can not open $user_detail_file: $!";
			my @user_content = <$U>;
			for (@user_content)
			{
				if ($_ =~ /email:/i) # get email address
				{
					my $email = $_;
					$email =~ s/ *email: *//ig;
					$email =~ s/ +$//g;
					chomp($email);
					if ($email =~ /^$original_email$/)
					{
						$email_legal = 1;
					}
				}
			}
			if (!$email_legal) # a right username, but with an unmatched email address
			{
				print start_form, "\n";
				print "Registered Username:\n", textfield('original_username'), "\n";
				print "Registered Email:\n", textfield('original_email'), "\n";
				print hidden(recover_account => "$recover_account"), "\n";
				print submit(value => Recover), "\n";
				print end_form, "\n";
				$display = "${display}Error:\nEmail is not valid";	
			}
			if ($user_legal && $email_legal) # both username and email are all good, send email for password recovery
			{
				$to = "$original_email";
				$from = "chengjia.xu@student.unsw.edu.au";
				$subject = "A Bitter recovery!";
				$message = "Please click the link to finish the password recovery:\n$ENV{SCRIPT_URI}?recover_account=1&confirm_recover=1&o_name=$original_username&o_email=$original_email";
					 
				open(MAIL, "|/usr/sbin/sendmail -t");
				print MAIL "To: $to\n";
				print MAIL "From: $from\n";
				print MAIL "Subject: $subject\n\n";
				print MAIL $message;

				$display = "${display}A very Bitter recovery email has ben sent to your email address: $original_email";
			}
		}
	}

	if (param('recover_account') && param('confirm_recover') && !param('new_password')) # password recovery step 3, email is clicked, begin recovering process, here you can recovery the password, or change to a new one
	{
		$original_username = param('o_name');
		my $user_detail_file = "$users_dir/$original_username/details.txt";
		if (-e $user_detail_file)
		{
			my $pwd;
			open my $U, "$user_detail_file" or die "can not open $user_detail_file: $!";
			my @user_content = <$U>;
			for (@user_content)
			{
				if ($_ =~ /password:/i) # get current password, it will display on the screen
				{
						$pwd = $_;
						$pwd =~ s/ *password: *//ig;
						$pwd =~ s/ +$//g;
						chomp($pwd);
						last;
				}
			}
			print start_form, "\n";
			print "New password:\n", textfield('new_password'), "\n";
			print hidden(recover_account => "$recover_account"), "\n";
			print hidden(original_username => "$original_username"), "\n";
			print submit(value => UpdatePassword), "\n";
			print end_form, "\n";
			$display = "<div class=\"bitter_heading\">In password recovering, user: ${original_username}</div>Your current password is: $pwd\n\nYou can now go back to Bitter home page to login again, or change to a new password";
		}
		else
		{
			$display = "<div class=\"bitter_heading\">Illegal operation!</div>";
		}
	}

	if  (param('recover_account') && param('new_password')) # password recovery step 4 (optional), user entered a new password
	{
		$display = "<div class=\"bitter_heading\">In password recovering, user: ${original_username}</div>";
		my $user_detail_file = "$users_dir/$original_username/details.txt";
		my $new_password = param('new_password');

		if (length($new_password) < 6) # if the new password is too short
		{
			print start_form, "\n";
			print "New password:\n", textfield('new_password'), "\n";
			print hidden(recover_account => "$recover_account"), "\n";
			print hidden(original_username => "$original_username"), "\n";
			print submit(value => UpdatePassword), "\n";
			print end_form, "\n";
			$display = "${display}Error:\nPassword too short, it should be longer than 6 characters";
		}
		else # a good password, write to the datails.txt file
		{
			open my $U, "<$user_detail_file" or die "can not open $user_detail_file: $!";
			my @user_content = <$U>;
			close $U;
			for (@user_content)
			{
				if ($_ =~ /password:/i)
				{
					$_ = "password: $new_password";
					last;
				}
			}
			open(my $B2, '>', $user_detail_file) or die "can not open $user_detail_file: $!";
			for (@user_content)
			{
				print $B2 "$_";
			}
			close $B2;
			$display = "${display}Password update compelted";
		}
	}

	if ($manage_account && (!param('new_latitude') && !param('new_longitude') && !param('new_suburb'))) # the interface of account management, where user can suspend/activate/delete his account and do other things
	{
		$username = param('login_name');
		print start_form, "\n";
		print submit('logout' => Logout), "\n";
		print submit('suspend_account' => 'Suspend Account'), "\n";
		print submit('delete_account' => 'Delete Account'), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print submit(back => Back), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";

		$display = "<div class=\"bitter_heading\">Account Management, user login as: $username</div>";
		$display = "${display}You can edit your user account information above. If you do not want to change a specific item, just leave it empty\n";

		print start_form, "\n";
		print "Home Latitude:\n", textfield('new_latitude'), "\n";
		print "Home Longitude:\n", textfield('new_longitude'), "\n";
		print "Home Suburb:\n", textfield('new_suburb'), "\n";
		print hidden(username => "$username"), "\n";
		print hidden(manage_account => "$manage_account"), "\n";
		print submit(value => Update), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print "Say something of yourself:\n", textarea(-name=>'create_profile', -rows=>1,-cols=>60), "\n";
		print submit(create_profile => 'Create Profile'), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";
	}

	if ($manage_account && (param('new_latitude') || param('new_longitude') || param('new_suburb'))) # user entered new account information
	{
		print start_form, "\n";
		print submit('logout' => Logout), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print submit(back => Back), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";

		my $new_latitude = param('new_latitude');
		$new_latitude =~ s/ +//;
		my $new_longitude = param('new_longitude');
		$new_longitude =~ s/ +//;
		my $new_suburb = param('new_suburb');
		$new_suburb =~ s/^ +//;
		$new_suburb =~ s/ +$//;
		my $user = glob("$users_dir/$username"); # path of the specific username
		$display = "<div class=\"bitter_heading\">Account Management, user login as: $username</div>";
		my $user_detail_file = "$user/details.txt";
		open my $U, "$user_detail_file" or die "can not open $user_detail_file: $!";
		my @user_content = <$U>;
		close $U;
		my @new_user_content;
		foreach my $line (@user_content) # write the new information to file
		{
			if ($line =~ /home_latitude:/i)
			{
				if ($new_latitude)
				{
					$line = "home_latitude: $new_latitude\n";
				}
			}
			elsif ($line =~ /home_longitude:/i)
			{
				if ($new_longitude)
				{
					$line = "home_longitude: $new_longitude\n";
				}
			}
			elsif ($line =~ /home_suburb:/i)
			{
				if ($new_suburb)
				{
					$line = "home_suburb: $new_suburb\n";
				}
			}
			push @new_user_content, $line;
		}

		open(my $B, '>', $user_detail_file) or die "can not open $user_detail_file: $!"; # write the new info to details.txt
		foreach my $line (@new_user_content)
		{
			print $B $line;
		}
		close $B;
		$display = "${display}Information update successfully\n";
	}

	if (param('manage_image')) # interface of image management, here user can upload/change/delete the avatar and background image
	{
		print start_form, "\n";
		print submit('logout' => Logout), "\n";
		print end_form, "\n";

		$username = param('login_name');
		print start_form, "\n";
		print submit(back => Back), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print filefield('avatar'), "\n", submit('Upload Avatar'), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print filefield('background'), "\n", submit('Upload Background'), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";

		my $user = glob("$users_dir/$username"); # path of the specific username, one is avatar (profile.jpg), the other one is background.jpg
		$display = "<div class=\"bitter_heading\">Image management, user login as: $username</div>";
		$display = "${display}Your currently have the following images, and you can delete/change them at any time\n\n";
		my $user_avatar = "$user/profile.jpg";
		my $user_background = "$user/background.jpg";
		my $image;
		my $background;
		if (-e $user_avatar) # if user has avatar, then display it
		{
			$image = "Avatar  <a href=\"bitter.cgi?delete_avatar=
				1$filename&login_name=$username\">[Delete avatar]</a>\n<img src=\"$user_avatar\" style=\"width:256px;height:256px;\">\n\n"
		}
		else
		{
			$image = "(no user avatar)\n";
		}
		if (-e $user_background) # if user has background, then display it
		{
			$background = "Background Image   <a href=\"bitter.cgi?delete_background=
				1$filename&login_name=$username\">[Delete background]</a>\n<img src=\"$user_background\" style=\"width:256px;height:256px;\">\n"
		}
		else
		{
			$background = "(no user background image)\n";
		}
		$display = "${display}$image$background";
	}

	if (param('avatar') || param('background')) # if user clicked upload avatar or background image
	{
		print start_form, "\n";
		print submit('logout' => Logout), "\n";
		print end_form, "\n";
		print start_form, "\n";
		print submit(back => Back), "\n";
		print hidden(username => "$username"), "\n";
		$display = "<div class=\"bitter_heading\">User login as: $username</div>";

		my $uploaded_file;
		my $destination_file;
		my $filename;
		my $updated_file;
		my $user = glob("$users_dir/$username"); # path of the specific username
		if (param('avatar'))
		{
			$uploaded_file = param('avatar');
			$destination_file = "$user/profile.jpg";
			$filename = 'avatar';
		}
		if (param('background'))
		{
			$uploaded_file = param('background');
			$destination_file = "$user/background.jpg";
			$filename = 'background';
		}

		my $query = new CGI; # write the image to destination file, in binmode, this will cover the original avatar/background (if it exists)
		my $upload_filehandle = $query->upload($filename);
		open my $IMAGE,">$destination_file";
		binmode $IMAGE;
		while (my $line = <$upload_filehandle>)
		{
			print $IMAGE $line;
		}
		close $IMAGE;

		$display = "${display}Upload successfully, your new $filename image is\n<img src=\"$destination_file\" style=\"width:256px;height:256px;\">\n"
	}

	if (param('delete_avatar')) # user delete avatar
	{
		$username = param('login_name');
		print start_form, "\n";
		print submit('logout' => Logout), "\n";
		print end_form, "\n";

		print start_form, "\n";
		print submit(back => Back), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";

		$display = "<div class=\"bitter_heading\">User login as: $username</div>";
		my $user = glob("$users_dir/$username"); # path of the specific username
		my $file = "$user/profile.jpg";
		unlink $file or die "$file is already deleted";
		$display = "${display}Your avatar has ben deleted successfully\n";

	}

	if (param('delete_background')) # user delete background
	{
		$username = param('login_name');
		print start_form, "\n";
		print submit('logout' => Logout), "\n";
		print end_form, "\n";

		print start_form, "\n";
		print submit(back => Back), "\n";
		print hidden(username => "$username"), "\n";
		print end_form, "\n";

		$display = "<div class=\"bitter_heading\">User login as: $username</div>";
		my $user = glob("$users_dir/$username"); # path of the specific username
		my $file = "$user/background.jpg";
		unlink $file or die "$file is already deleted";
		$display = "${display}Your background image has been deleted successfully\n";
	}

	if (param('suspend_account')) # move file from /user/xxxxx/ to /suspend/xxxxx/, a suspended account cannot be searched, but the bleats still can be viewed by followers, also still can be add/delete from listens
	{
		my @user_files = sort(glob("$users_dir/$username/*")); # array of files of a user
		my @user_attachments = sort(glob("$users_dir/$username/attachment/*"));
		my $suspend_path = "$suspend_dir/$username";
		if (!(-e $suspend_path))
		{
			mkdir "$suspend_path" or die "Unable to create $suspend_path: $!";
		}
		if (-e "$users_dir/$username/attachment") # if the user has attachments, move this part firstly
		{
			if (!(-e "$suspend_path/attachment"))
			{
				mkdir "$suspend_path/attachment" or die "Unable to create $suspend_dir/$username/attachment: $!";
			}
			for my $file (@user_attachments)
			{
				chomp($file);
				my $filename = $file;
				$filename =~ s/.*\///;
				move($file, "$suspend_path/attachment/$filename");
			}
			rmdir "$users_dir/$username/attachment" or die "Unable to delete $users_dir/$username/attachment: $!";
		}
		for my $file (@user_files)
		{
			chomp($file);
			my $filename = $file;
			$filename =~ s/.*\///;
			move($file, "$suspend_path/$filename");
		}
		rmdir "$users_dir/$username" or die "Unable to delete $users_dir/$username: $!";
		$display = "<div class=\"bitter_heading\">User: $username is under suspending now, wish you come back to Bitter one day!</div>";
	}

	if (param('activate_account')) # move file from /suspend/xxxxx/ to /user/xxxxx/
	{
		my @suspend_files = sort(glob("$suspend_dir/$username/*")); # array of files of a user
		my @suspend_attachments = sort(glob("$suspend_dir/$username/attachment/*"));
		my $user_path = "$users_dir/$username";
		if (!(-e $user_path))
		{
			mkdir "$user_path" or die "Unable to create $user_path: $!";
		}
		if (-e "$suspend_dir/$username/attachment") # if the user has attachments, move this part firstly
		{
			if (!(-e "$user_path/attachment"))
			{
				mkdir "$user_path/attachment" or die "Unable to create $users_dir/$username/attachment: $!";
			}
			for my $file (@suspend_attachments)
			{
				chomp($file);
				my $filename = $file;
				$filename =~ s/.*\///;
				move($file, "$user_path/attachment/$filename");
			}
			rmdir "$suspend_dir/$username/attachment" or die "Unable to delete $suspend_dir/$username/attachment: $!";
		}
		for my $file (@suspend_files)
		{
			chomp($file);
			my $filename = $file;
			$filename =~ s/.*\///;
			move($file, "$user_path/$filename");
		}
		rmdir "$suspend_dir/$username" or die "Unable to delete $suspend_dir/$username: $!";
		$display = "<div class=\"bitter_heading\">User: $username is activated now, welcome home! Please go back to home page and login again</div>";
	}

	if (param('delete_account')) # delete files from the user directory, then delete the directory itself
	{
		if (-e "$users_dir/$username/attachment")
		{
			my @user_files = sort(glob("$users_dir/$username/attachment/*")); # array of files of a user
			for my $file (@user_files)
			{
				unlink $file;
			}
			rmdir "$users_dir/$username/attachment" or die "Unable to delete $users_dir/$username/attachment: $!";
		}
		if (-e "$notification_dir/$username")
		{
			my @user_files = sort(glob("$notification_dir/$username/*")); # array of files of a user
			for my $file (@user_files)
			{
				unlink $file;
			}
			rmdir "$notification_dir/$username" or die "Unable to delete $notification_dir/$username: $!";	
		}
		my @user_files = sort(glob("$users_dir/$username/*")); # array of files of a user
		for my $file (@user_files)
		{
			unlink $file;
		}
		rmdir "$users_dir/$username" or die "Unable to delete $users_dir/$username: $!";
		$display = "<div class=\"bitter_heading\">User: $username, your account has been deleted, wish you come back to Bitter one day!</div>";
	}




return <<eof
<div class="bitter_user_details">
$display
</div>
$display_bleat
<p>
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
<a href="bitter.cgi">Bitter, where you can feel bitter!</a>
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

