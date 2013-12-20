#!/usr/bin/env perl
# -*- cperl -*-
=head1 NAME

defminer.cgi

=head1 SYNOPSYS

 RCS:$Id: parsCit.cgi,v 1.1 2004/12/23 18:03:11 min Exp min $

=head1 DESCRIPTION

BUG: lvl 2 classification in odp done wrong, requires new architecture of database

=head1 HISTORY

 ORIGIN: created from templateApp.pl version 3.4 by Min-Yen Kan <kanmy@comp.nus.edu.sg>

 RCS:$Log: parsCit.cgi,v $
 RCS:

=cut

require 5.0;
use Getopt::Std;
use CGI;

### USER customizable section
my $tmpfile .= $0; $tmpfile =~ s/[\.\/]//g;
$tmpfile .= $$ . time;
if ($tmpfile =~ /^([-\@\w.]+)$/) { $tmpfile = $1; }                 # untaint tmpfile variable
$tmpfile = "/tmp/" . $tmpfile;
$0 =~ /([^\/]+)$/; my $progname = $1;
my $outputVersion = "1.0";
my $baseDir = "/home/wing.nus/tools/citationTools/raz//";
my $binDir = "$baseDir/bin/";
my $libDir = "$baseDir/lib/";
my $logFile = "$libDir/cgiLog.txt";
my $seed = $$;
my $debug = 0;

my @zones = ("BKG","OTH","OWN","AIM","TXT","CTR","BAS");

my $loadThreshold = 0.5;
my $loadKey = "wing";
### END user customizable section

$| = 1;								    # flush output

### Ctrl-C handler
sub quitHandler {
  print STDERR "\n# $progname fatal\t\tReceived a 'SIGINT'\n# $progname - exiting cleanly\n";
  exit;
}

### HELP Sub-procedure
sub Help {
  print STDERR "usage: $progname -h\t\t\t\t[invokes help]\n";
  print STDERR "       $progname -v\t\t\t\t[invokes version]\n";
  print STDERR "       $progname [-q] filename(s)...\n";
  print STDERR "Options:\n";
  print STDERR "\t-q\tQuiet Mode (don't echo license)\n";
  print STDERR "\n";
  print STDERR "Will accept input on STDIN as a single file.\n";
  print STDERR "\n";
}

### VERSION Sub-procedure
sub Version {
  if (system ("perldoc $0")) {
    die "Need \"perldoc\" in PATH to print version information";
  }
  exit;
}

sub License {
  print STDERR "# Copyright 2004 \251 by Min-Yen Kan\n";
}

my $q = new CGI;
print "Content-Type: text/html\n\n";
print <<END;
<HTML><HEAD><TITLE>Argumentative Zoning for Raw Text</TITLE>
<LINK REL="stylesheet" type="text/css" href="zoning.css" />
END
printDivFunction();
print "</HEAD><BODY>";


###
### MAIN program
###

my $inputMode = $q->param('inputMode');
my $stages = $q->param('stages');
my $filename = "";
my $key = "";
if ($q->param('key') ne "") {
  $key = $q->param('key');
}

if (loadTooHigh() && $key ne $loadKey) {
  printLoadTooHigh();
  `rm -f $tmpfile*`;
  exit;
}

if ($q->param('text') ne "") {					    # get form textarea
  my $textLine = $q->param('text');

  @text = split (/\n/,$textLine);
  open (OF, ">$tmpfile\.inputFile");
  for (my $i = 0; $i <= $#text; $i++) {
    print OF "$text[$i]\n";
  }
  close (OF);
} elsif ($q->param('datafile') ne "") {				    # get uploaded text file
  my $file = $q->param('datafile');
  $filename = $file;

  # Copy a binary file to somewhere safe
  open (OUTFILE,">$tmpfile\.inputFile");
  while ($bytesread = read($file,$buffer,1024)) {
    print OUTFILE $buffer;
  }
  close $file;
} else {
  print "You must input some data.  <A HREF=\"index.html\">Start over.</A>\n";
  exit;
}

open (LOGFILE, ">>$logFile") || die "# $progname fatal\t\tCouldn't open logfile file \"$logFile\"";
print LOGFILE "# Executed for REMOTE_ADDR " . $q->remote_addr() . " at " . localtime(time) . "\n";
for ($i = 0; $i <= $#text; $i++) {
  print LOGFILE "$text[$i]\n";
}
close (LOGFILE);

# run argumentative zoning pipeline
print "<H2>Execution Progress</H2>";
print "[ <a href=\"index.html\">Back to zoning home page</a> ]<BR/>";
print "Using input mode <B>$inputMode!</B><BR/>";
if ($filename ne "") { print "Operating on your uploaded file <B>$filename</B><BR/>"; }
else { print "Operating on your input box input<BR/>"; }

my $inputFile = "$tmpfile\.inputFile";
my $annotFlag = "";
my $buf = "";
if ($inputMode eq "annot") {
  $buf = "$binDir/annot2txt.pl $inputFile > $tmpfile\.txt\n";
  print $buf . "<BR/>";
  `$buf`;
  $inputFile = "$tmpfile\.txt";
  $annotFlag = "-a"
} else {
  $annotFlag = "-s $tmpfile\.delimit";
}

$buf = "$binDir/txt2tag.pl $annotFlag $inputFile > $tmpfile\.tag\n";
print localtime(time) . " [1] $buf [ <A HREF=\"javascript:toggleLayer(\'hidden1\')\">Show POS tags</A> ] <BR/>";
$_ = `$buf`;
printHiddenDiv("hidden1", "$tmpfile\.tag");

$buf = "$binDir/tag2feats.pl $tmpfile\.tag > $tmpfile\.feats\n";
print localtime(time) . " [2] $buf [ <A HREF=\"javascript:toggleLayer(\'hidden2\')\">Show features generated</A> ] <BR/>";
$_ = `$buf`;
printHiddenDiv("hidden2", "$tmpfile\.feats");

$buf = ($inputMode eq "annot") ?   # select which trained model to use
  "$binDir/maxent -m $libDir/model.withContext.all -p $tmpfile\.feats --detail -o $tmpfile\.detail" :
  "$binDir/maxent -m $libDir/model.noContext.all -p $tmpfile\.feats --detail -o $tmpfile\.detail";
print localtime(time) . " [3] $buf <BR/>";
$_ = `$buf`;

$buf = "$binDir/detail2out2.pl $tmpfile\.detail > $tmpfile\.out2";
print localtime(time) . " [4] $buf <BR/>";
$_ = `$buf`;

if ($inputMode eq "rawText" && $stages eq "2") {
  print "<H3> Doing second stage </H3>";

  # do second round tagging
  $buf = "paste $tmpfile\.out2 $tmpfile\.feats > $tmpfile\.result1";
  print localtime(time) . " [5] $buf [ <A HREF=\"javascript:toggleLayer(\'hidden3\')\">Show first round tagging</A> ] <BR/>";
  $_ = `$buf`;
  printHiddenDiv("hidden3", "$tmpfile\.result1");

  $buf = "$binDir/mergeDelimitOut.pl $tmpfile\.delimit $tmpfile\.out2 > $tmpfile\.txt2";
  print localtime(time) . " [6] $buf <BR/>";
  $_ = `$buf`;

  $buf = "$binDir/txt2tag.pl -a $tmpfile\.txt2 > $tmpfile\.tag2\n";
  print localtime(time) . " [7] $buf <BR/>";
  $_ = `$buf`;

  $buf = "$binDir/tag2feats.pl $tmpfile\.tag2 > $tmpfile\.feats2\n";
  print localtime(time) . " [8] $buf [ <A HREF=\"javascript:toggleLayer(\'hidden4\')\">Show features generated</A> ] <BR/>";
  $_ = `$buf`;
  printHiddenDiv("hidden4", "$tmpfile\.feats2");

  $buf = "$binDir/maxent -m $libDir/model.withContext.all -p $tmpfile\.feats2 --detail -o $tmpfile\.detail2";
  print localtime(time) . " [9] $buf <BR/>";
  $_ = `$buf`;

  $buf = "$binDir/detail2out2.pl $tmpfile\.detail2 > $tmpfile\.out3";
  print localtime(time) . " [10] $buf <BR/>";
  $_ = `$buf`;

  $buf = "paste $tmpfile\.out3 $tmpfile\.feats > $tmpfile\.result2";
  print localtime(time) . " [11] $buf <BR/>";
  $_ = `$buf`;

  printOutput("$tmpfile\.result2");
} else {
  $buf = "paste $tmpfile\.out2 $tmpfile\.feats > $tmpfile\.result";
  print localtime(time) . " [5] $buf <BR/>";
  $_ = `$buf`;
  printOutput("$tmpfile\.result");
}


print "<HR><H5>Generated on " . localtime(time) . " for a user at IP address " . $q->remote_addr() . " </H5>";

# remove temporary files
`rm -f $tmpfile.*`;

###
### END of main program
###

sub printKey {
  print "<P> Key: \n";
  foreach my $zone (@zones) {
    print "<SPAN CLASS=\"$zone\"> $zone </SPAN> &nbsp;&nbsp;&nbsp;";
  }
  print "</P>\n";
}


# print output - in order
sub printOutput {
  my @spans;
  my %zoneHash;
  my $filename = shift;

  print "<H2>Output</H2>";
  print "[ <a href=\"index.html\">Back to zoning home page</a> ]<BR/>";

  # print key
  printKey();
  if ($inputMode eq "rawText") {
    print "<P>N.B. - Since you are using raw text as input we cannot show you what is wrong with the text, just the predicted markup.</P>\n";
  } else { # input style = annot
    print "<P>Hover any span to see the top 2 predicted classes.  Red text indicates that the system got the wrong answer, as compared to the correcte answers in the uploaded .annot file.</P>";
  }

  open (IF, $filename) || die;
  my $counter = 0;
  while (<IF>) {
    chop;
    my ($guess,$conf,$guess2,$conf2,$buf) = split (/\t/);
    my ($answer,$feats) = split (/ /,$buf,2);
    my $line = $feats;
    $line =~ s/REL_POSITION.+//;		     # chop off feature vector
    $line =~ s/&/&amp;/g;					      # escape
    $line =~ s/</&lt;/g;				 # escape BUG, use lib
    $line =~ s/>/&gt;/g;					      # escape
    $line = "[" .  $counter++ . "] $line";
    if ($answer ne "UNDEFINED" && $answer ne $guess) {	 # wrong guess
      $spans[$counter] = "<SPAN CLASS=\"$guess\" title=\"$guess($conf) $guess2($conf2) - incorrect\">$answer <SPAN CLASS=\"wrong\">$line</SPAN></SPAN>\n";
    } else {					      # correct answer
      $spans[$counter] = "<SPAN CLASS=\"$guess\" title=\"$guess($conf) $guess2($conf2)\">$line</SPAN>\n";
    }
    push (@{$zoneHash{$guess}{$conf}},$counter);
    print $spans[$counter];
  }
  close (IF);
  printKey();

  # Output by zone
  print "<H3>Output - by zone type, ordered by confidence</H3>";
  foreach my $zone (@zones) {
    print "<SPAN CLASS=\"$zone\"> $zone </SPAN><P><TABLE WIDTH=\"100%\">";
    foreach my $conf (sort {$b <=> $a} (keys %{$zoneHash{$zone}})) {
      foreach my $line (@{$zoneHash{$zone}{$conf}}) {
	print "<TR><TD>";
	printf("%3.3e",$conf);
	print "</TD><TD>$spans[$line]</TD></TR>";
      }
    }
    print "</TABLE></P>";
  }
}

sub printDivFunction {
  # from http://www.netlobo.com/div_hiding.html on Thu Dec 20 00:30:50 SGT 2007
print <<FUNCTION;
<script type="text/javascript">
function toggleLayer( whichLayer )
  {
  var elem, vis;
  if( document.getElementById ) // this is the way the standards work
    elem = document.getElementById( whichLayer );
  else if( document.all ) // this is the way old msie versions work
      elem = document.all[whichLayer];
  else if( document.layers ) // this is the way nn4 works
    elem = document.layers[whichLayer];
  vis = elem.style;
  // if the style.display value is blank we try to figure it out here
  if(vis.display==''&&elem.offsetWidth!=undefined&&elem.offsetHeight!=undefined)
    vis.display = (elem.offsetWidth!=0&&elem.offsetHeight!=0)?'block':'none';
  vis.display = (vis.display==''||vis.display=='block')?'none':'block';
}
</script>
FUNCTION
}

sub printHiddenDiv {
  my $divName = shift;
  my $fileName = shift;
  open (IF,$fileName) || die;
  print "<DIV ID=\"$divName\" CLASS=\"hidden\" STYLE=\"display:none;\"><PRE>";
  while (<IF>) {
    s/&/&amp;/g;						      # escape
    s/</&lt;/g;					 # escape BUG, use lib
    s/>/&gt;/g;						      # escape
    print;
  }
  print "</PRE></DIV>";
  close (IF);
}

sub loadTooHigh {
my $load = `uptime`;
  $load =~ /load average: ([\d.]+)/i;
  my $load = $1;
  print "Load on server: $load<br/>";
  if ($load > $loadThreshold) { return 1; } else { return 0; }
}

sub printLoadTooHigh {
  print <<END;
<P>Sorry, the load on this machine is currently too high.  Public demos are only run when computing load is available.  <A HREF="index.html">Please try back again later</A>.  Thanks!
END
}
