+++
Categories = ["debian", "linux"]
date = "2016-06-04T00:13:28+02:00"
title = "No more unencrypted emails to gpg contacts"

+++

I have been using mutt for about half a year already and I'm very happy with it.
The previous email client I used was Thunderbird (with the Enigmail extension to
handle GPG).  There were two main reasons that made me switch.

The first one was that I often would like to check my email while I'm offline,
and it seems that Thunderbird is not very good at this.  Sometimes not all my
email would have been downloaded (just the headers), and I also found it
frustrating that after marking more than 50 emails as read while offline, they
would be marked as unread again once I went back online.  With mutt I'm using
mbsync (which apparently is faster than offlineimap) to sync my email to a local
folder with a cron job.  I couldn't be happier.

The other issue was that I like having many filters, and it was tedious to
customize filters in Thunderbird:  there's no way to copy a filter and modify
it, and there's a limit in the combinations of ANDs and ORs for fields.  I'm
using procmail now, which allows me save the filter configuration in plaintext
and define patterns with more flexibility.

The setup for mutt took several weeks, but I never felt that I couldn't
accomplish what I wanted (unlike in Thunderbird).  I'm using mutt with several
python and bash scripts that I wrote.

But the reason for this post is an issue that I believe happens in every email
client (or should I say, MUA, to be more precise).  I've seen it happening to
people using both Thunderbird and mutt, and I bet it has happened in other
cases: sending an email to someone for which you have their GPG key unencrypted
unwillingly.  I've seen this happening in email replies with several
participants: after a few encrypted messages are exchanged, someone replies in
the clear, quoting all the previous messages.  I tried to avoid this by
configuring mutt to encrypt and sign by default, forcing me to set sign only
manually before sending every email that I can't send encrypted (I'd like to
send all my emails encrypted, but not everybody has a GPG key :( ).

So what happened?  I got so used to sending many unencrypted emails that I would
press "P S" (PGP setting, Sign only) before sending emails as a reflex act.  And
I sent an email unencrypted to a friend for which I have his GPG key :(

So I thought: It's a very rare case to want to send an unencrypted email to
someone for which you have their GPG key.  I think extensions like Enigmail
should give you a warning when this happens, to alert you about it.  In my case,
I solved it with a python script that inspects the email, and, if it's
unencrypted and the recipient/s is/are in your GPG keyring it warns you about it
and returns an error.  The script stores a temporary file with the Message-ID so
that if you run it again with the same email it will properly send the email
without returning an error.

Now, I only needed to configure mutt to use this script as the sendmail command:

```
per_account:set sendmail  = "$HOME/bin/check-mail-gpg /usr/bin/msmtp -a $my_email"
```

And here goes the python script `check-mail-gpg`:

{{< highlight python3 >}}
#! /usr/bin/python3

import os
import sys
import subprocess
import email.parser
from email.header import decode_header
from email.utils import parseaddr

STATUS_FILE = '/tmp/check-mail-gpg.tmp'

def dec(header):
    head = decode_header(header)
    if len(head) == 1 and head[0][1] == None:
        return head[0][0]
    else:
        return ''.join([h.decode(enc) if enc else h.decode('ascii') \
                for (h,enc) in head])

def send_mail(mail):
    print('Calling external email client to send the email...')
    #return -1 # testing mode
    p = subprocess.Popen(sys.argv[1:], stdin=subprocess.PIPE)
    p.stdin.write(mail.encode('utf-8'))
    p.stdin.close()
    return p.wait()

def main():
    mail = sys.stdin.read()
    heads = email.parser.Parser().parsestr(mail, headersonly=True)
    content = heads['Content-Type'].split(';')[0].strip()
    print('Content is:', content)

    if content == 'multipart/encrypted':
        print('Ok: encrypted mail, we can return now...')
        sys.exit(send_mail(mail))

    addrs = [parseaddr(addr) for addr in heads['To'].split(',')]
    print('Found emails:', addrs)

    gpg_cnt = 0
    for name, addr in addrs:
        print('Looking for', addr, 'in the keyring...')
        res = subprocess.call(['gpg', '--list-keys', addr],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res == 0:
            gpg_cnt += 1

    if gpg_cnt == 0:
        print('Ok: no email found in the gpg keyring, we can return now...')
        sys.exit(send_mail(mail))

    if not os.path.exists(STATUS_FILE):
        open(STATUS_FILE, 'w').close()

    msg_id = heads['Message-ID']
    msg_id_prev = ''
    with open(STATUS_FILE, 'r') as f:
        msg_id_prev = f.read()

    if msg_id.strip() == msg_id_prev.strip():
        sys.exit(send_mail(mail))
    else:
        with open(STATUS_FILE, 'w') as f:
            f.write(msg_id)
        print('Alert: trying to send an unencrypted email to', addrs,
                ', for which some gpg keys were found in the keyring!')
        print('Try again if you are sure to send this message unencrypted.')
        sys.exit(1)

if __name__ == '__main__':
    main()
{{< /highlight >}}

# Update

I've been told about the option `crypt_opportunistic_encrypt` in mutt, which
provides a feature very similar to what I was looking for.  This option will
automatically enable encryption when the recipient has a GPG key in your
keyring.

From mutt's man page:

> 3.41. crypt_opportunistic_encrypt
> 
> Type: boolean Default: no
> 
> Setting this variable will cause Mutt to automatically enable and disable
> encryption, based on whether all message recipient keys can be located by
> mutt.
> 
> When this option is enabled, mutt will determine the encryption setting each
> time the TO, CC, and BCC lists are edited. If $edit_headers is set, mutt will
> also do so each time the message is edited.
> 
> While this is set, encryption settings can't be manually changed. The pgp or
> smime menus provide an option to disable the option for a particular message.
> 
> If $crypt_autoencrypt or $crypt_replyencrypt enable encryption for a message,
> this option will be disabled for the message. It can be manually re-enabled in
> the pgp or smime menus. (Crypto only) 
