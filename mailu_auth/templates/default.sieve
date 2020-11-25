require "variables";
require "vacation";
require "fileinto";
require "envelope";
require "mailbox";
require "imap4flags";
require "regex";
require "relational";
require "date";
require "comparator-i;ascii-numeric";
require "spamtestplus";
require "editheader";
require "index";

if header :index 2 :matches "Received" "from * by * for <*>; *"
{
  deleteheader "Delivered-To";
  addheader "Delivered-To" "<${3}>";
}

if spamtest :percent :value "gt" :comparator "i;ascii-numeric"  "80"
{
  setflag "\\seen";
  fileinto :create "Junk";
  stop;
}

if exists "X-Virus" {
  discard;
  stop;
}
