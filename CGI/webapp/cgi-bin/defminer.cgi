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
use Cwd;

### USER customizable section
my $tmpfile .= $0; $tmpfile =~ s/[\.\/]//g;
$tmpfile .= $$ . time;
if ($tmpfile =~ /^([-\@\w.]+)$/) { $tmpfile = $1; }                 # untaint tmpfile variable
my $basename=$tmpfile;
$tmpfile = "/tmp/" . $tmpfile;
$0 =~ /([^\/]+)$/; my $progname = $1;
my $outputVersion = "1.0";
#my $baseDir = "/home/wing.nus/tools/citationTools/raz//";
my $baseDir = "/home/yiping/defminer-distribution/";
my $binDir = "$baseDir/bin/";
my $libDir = "$baseDir/lib/";
my $logDir = "$baseDir/log/";
my $logFile = "$logDir/cgiLog.txt";
my $seed = $$;
my $debug = 0;

my @zones = ("TERM","DEF","O");

my $loadThreshold = 0.5;
my $loadKey = "secrete";
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
<HTML><HEAD><TITLE>DefMiner</TITLE>
<LINK REL="stylesheet" type="text/css" href="../zoning.css" />
END
printDivFunction();
print "</HEAD><BODY>";


###
### MAIN program
###

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
  print "You must input some data.  <A HREF=\"../index.html\">Start over.</A>\n";
  exit;
}

open (LOGFILE, ">>$logFile") || die "# $progname fatal\t\tCouldn't open logfile file \"$logFile\"";
print LOGFILE "# Executed for REMOTE_ADDR " . $q->remote_addr() . " at " . localtime(time) . "\n";
for ($i = 0; $i <= $#text; $i++) {
  print LOGFILE "$text[$i]\n";
}
close (LOGFILE);

# run defminer pipeline
print "<H2>Execution Progress</H2>";
print "[ <a href=\"../index.html\">Back to DefMiner home page</a> ]<BR/>";
if ($filename ne "") { print "Operating on your uploaded file <B>$filename</B><BR/>"; }
else { print "Operating on your input box input<BR/>"; }

my $inputFile = "$tmpfile\.inputFile";
my $resultFile = "$tmpfile\_defminer\/$basename\.annotated";
my $buf = "";

#$buf = "java -Xmx4g -cp $baseDir/preprocess/integratedParser/bin:$baseDir/preprocess/integratedParser/lib/* main.IntegratedParser $inputFile >$logFile\n";
chdir($baseDir) or die "cannot change: $!\n"; 
$buf = "sh $baseDir/DefMiner $inputFile";
print localtime(time) . " [1] $buf <BR/>";
$_ = `$buf`;

print "<HR><H5>Generated on " . localtime(time) . " for a user at IP address " . $q->remote_addr() . " </H5>";

printOutput("$tmpfile");

# remove temporary files

`rm -f -r /tmp/$basename*`;

###
### END of main program
###

sub printKey {
  print "<P> Key: \n";

  print "<SPAN CLASS=\"$zone\"  STYLE=\'background: yellow\'> TERM </SPAN> &nbsp;&nbsp;&nbsp;";

  print "<SPAN CLASS=\"$zone\"  STYLE=\'background: cyan\'> DEFINITION </SPAN> &nbsp;&nbsp;&nbsp;";

  print "<SPAN CLASS=\"$zone\"> O </SPAN> &nbsp;&nbsp;&nbsp;";

  print "</P>\n";
}


# print output - in order
sub printOutput {
  my @spans;
  my %zoneHash;
  my $filename = shift;

  print "<H2>Output</H2>";
  print "[ <a href=\"../index.html\">Back to DefMiner home page</a> ]<BR/>";

  # print key
  printKey();

  $replace=".inputFile";
  $new="_defminer";

  $filename =~ s/$replace/""/;
  #print("<BR/>\$filename : $filename<BR/>");
  
  $filepath="$filename$new\/$basename$new\.annotated";

  #print("<BR/>Result file from: $filepath<BR/>");
  open (IF, $filepath) || die;

  while (my $row = <IF>) {
    chomp $row;
    print "<P>$row</P>";
  }
  close (IF);
  #printKey();

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
<P>Sorry, the load on this machine is currently too high.  Public demos are only run when computing load is available.  <A HREF="../index.html">Please try back again later</A>.  Thanks!
END
}
