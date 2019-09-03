+++
Categories = ["alpine", "raspberry pi", "git", "linux"]
date = "2016-10-21T15:14:27-07:00"
title = "Raspberry Pi: git server (cgit with lighttpd)"

+++

# Introduction

In this post I will explain what's required to set up a git server.  We'll use
[cgit](https://git.zx2c4.com/cgit/) to provide a web interface and also allow
cloning/pulling through HTTP.  ssh will also be available for cloning/pulling
and pushing.

We'll setup two groups of repositories: a public and a private one.

# Cgit

First of all, we'll create a *git* user and move it's home to the encrypted
partition.  For convenience we'll also link that home directory to `/git`.  This
will be useful to have nice paths for our repositories.

{{< highlight bash >}}
adduser git
lbu add /home/git/

rmdir /home/git
ln -sf /mnt/disk/git /home/
cp -R /home/green/.ssh /home/git/.ssh
chown -R git:git /home/git/
ln -s /home/git/ /git
{{< /highlight >}}

Finally we install git, cgit and highlight (to provide code highlighting in
cgit).

{{< highlight bash >}}
apk add highlight git cgit
{{< /highlight >}}

cgit comes with a default script that will call highlight, but unfortunately
it's expecting version 2 of highlight.  We'll copy the script and change it to
use the argument format of version 3 of highlight (the line is already there, we
just comment the version 2 and uncomment the version 3).

{{< highlight bash >}}
cp /usr/lib/cgit/filters/syntax-highlighting.sh /usr/lib/cgit/filters/syntax-highlighting3.sh
vim /usr/lib/cgit/filters/syntax-highlighting3.sh
{{< /highlight >}}

{{< highlight diff >}}
--- /usr/lib/cgit/filters/syntax-highlighting.sh
+++ /usr/lib/cgit/filters/syntax-highlighting3.sh
@@ -115,7 +115,7 @@
 # found (for example) on EPEL 6.
 #
 # This is for version 2
-exec highlight --force -f -I -X -S "$EXTENSION" 2>/dev/null
+#exec highlight --force -f -I -X -S "$EXTENSION" 2>/dev/null

 # This is for version 3
-#exec highlight --force -f -I -O xhtml -S "$EXTENSION" 2>/dev/null
+exec highlight --force -f -I -O xhtml -S "$EXTENSION" 2>/dev/null
{{< /highlight >}}

{{< highlight bash >}}
lbu add /usr/lib/cgit/filters/syntax-highlighting3.sh
{{< /highlight >}}

Highlight uses css to color the code, so we need to add some lines specifying
the colors we want to the css file cgit uses.

{{< highlight bash >}}
cp /usr/share/webapps/cgit/cgit.css /usr/share/webapps/cgit/cgit-highlight.css
vim /usr/share/webapps/cgit/cgit-highlight.css
{{< /highlight >}}

{{< highlight diff >}}
--- /usr/share/webapps/cgit/cgit.css
+++ /usr/share/webapps/cgit/cgit-highlight.css
@@ -809,3 +809,20 @@
 div#cgit table.ssdiff td.space div {
        min-height: 3em;
 }
+
+body.hl { background-color:#e0eaee; }
+pre.hl  { color:#000000; background-color:#e0eaee; font-size:10pt; font-family:'Courier New',monospace;}
+.hl.num { color:#b07e00; }
+.hl.esc { color:#ff00ff; }
+.hl.str { color:#bf0303; }
+.hl.pps { color:#818100; }
+.hl.slc { color:#838183; font-style:italic; }
+.hl.com { color:#838183; font-style:italic; }
+.hl.ppc { color:#008200; }
+.hl.opt { color:#000000; }
+.hl.ipl { color:#0057ae; }
+.hl.lin { color:#555555; }
+.hl.kwa { color:#000000; font-weight:bold; }
+.hl.kwb { color:#0057ae; }
+.hl.kwc { color:#000000; font-weight:bold; }
+.hl.kwd { color:#010181; }
{{< /highlight >}}

{{< highlight bash >}}
lbu add /usr/share/webapps/cgit/cgit-highlight.css
{{< /highlight >}}

As mentioned in the introduction, we will setup two folders, one for private repositories and the other one for public ones.

{{< highlight bash >}}
cd /mnt/disk
mkdir -p git/pub
mkdir -p git/priv
{{< /highlight >}}

For our setup we will use a general cgit configuration files, and two
specialized ones for the public and private folders.

{{< highlight bash >}}
mkdir /etc/cgit
{{< /highlight >}}

```
cat << EOF > /etc/cgit/cgitrc
css=/cgit/cgit-highlight.css
logo=/cgit/cgit.png
source-filter=/usr/lib/cgit/filters/syntax-highlighting3.sh
enable-git-config=1
enable-index-owner=0
enable-commit-graph=1
enable-index-links=1
enable-log-linecount=1
enable-log-filecount=1
#cache-size=512
robots=noindex, nofollow
root-title=Dhole's git repositories
root-desc=my personal repositories
remove-suffix=1
clone-prefix=https://lizard.kyasuka.com/cgit/cgit.cgi ssh://git@lizard.kyasuka.com:
EOF
```

```
cat << EOF > /etc/cgit/cgitrc.public
include=/etc/cgit/cgitrc
clone-prefix=https://lizard.kyasuka.com/cgit/cgit.cgi ssh://git-kyasuka/git/pub
section=Public
scan-path=/mnt/distk/git/pub/
EOF
```

```
cat << EOF > /etc/cgit/cgitrc.private
include=/etc/cgit/cgitrc
clone-prefix=https://lizard.kyasuka.com/private/cgit/cgit.cgi ssh://git-kyasuka/git/priv
section=Private
scan-path=/mnt/disk/git/priv/
EOF
```

And finally, we create a new configuration file for lighttpd which will call
cgit via the cgi interface.  We are using the public and private configurations
by setting the `CGIT_CONFIG` environment variable depending on the url path.
Remember to follow the previous post to add http auth to the urls that start
with `/private`.

```
cat << EOF > /etc/lighttpd/cgit.conf
server.modules += ("mod_redirect",
                   "mod_alias",
                   "mod_cgi",
                   "mod_fastcgi",
                   "mod_rewrite",
                   "mod_alias",)

var.webapps = "/usr/share/webapps/"
$HTTP["url"] =~ "^/cgit" {
        setenv.add-environment += ( "CGIT_CONFIG" => "/etc/cgit/cgitrc.public" )
        server.document-root = webapps
        server.indexfiles = ("cgit.cgi")
        cgi.assign = ("cgit.cgi" => "")
        mimetype.assign = ( ".css" => "text/css" )
}
url.redirect = (
        "^/git/(.*)$" => "/cgit/cgit.cgi/$1",
)
$HTTP["url"] =~ "^/private/cgit" {
        #url.rewrite-once = ( "^/private/cgit/(.*)" => "/cgit/$1" )
        alias.url = ( "/private/" => "/usr/share/webapps/" )
        setenv.add-environment += ( "CGIT_CONFIG" => "/etc/cgit/cgitrc.private" )
        server.document-root = webapps
        server.indexfiles = ("cgit.cgi")
        cgi.assign = ("cgit.cgi" => "")
        mimetype.assign = ( ".css" => "text/css" )
}
EOF
```

{{< highlight bash >}}
vim /etc/lighttpd/lighttpd.conf
{{< /highlight >}}

{{< highlight bash >}}
...
...
# {{{ includes
...
include "cgit.conf"
...
# }}}
...
...
{{< /highlight >}}

We commit every file to permanent storage and restart the lighttpd server.

{{< highlight bash >}}
lbu commit
rc-service lighttpd start
{{< /highlight >}}

We should be able to visit the cgit interface from a browser now.

# Git usage

To automate making new repositories I wrote the following simple script:

```
cat << EOF > /home/git/new-repo.sh
```
{{< highlight bash >}}
#! /bin/sh

folder=$1
name=$2
desc="$3"

if [ "$#" -ne 3 ]
then
        echo "Usage: $0 {pub|priv} name description"
        exit 1
fi

if [ ! -d "$folder" ]
then
        echo "Group $folder doesn't exist.  use pub/priv."
        exit 2
fi

if [ -d "$folder/$name".git ]
then
        echo "$folder/$name already exists"
        exit 3
fi

if [ "$desc" == "" ]
then
        echo "Please, provide a description in the 3rd argument."
        exit 4
fi

cd "$folder"
mkdir "$name".git
cd "$name".git
git init --bare
echo "$desc" > description

echo "$folder/$name is ready."
echo ""
echo "  Create a new repository"
echo ""
echo "git clone ssh://git-kyasuka/git/$folder/$name.git"
echo "cd $name"
echo "touch README.md"
echo "git add README.md"
echo "git commit -m \"add README\""
echo "git push -u origin master"
echo ""
echo "  Existing folder or Git repository"
echo ""
echo "cd existing_folder"
echo "git init"
echo "git remote add origin ssh://git-kyasuka/git/$folder/$name.git"
echo "git add ."
echo "git commit"
echo "git push -u origin master"
{{< /highlight >}}
```
EOF
```

Now, to create a new git repository I just do the following from my local
machine:

{{< highlight bash >}}
ssh git@lizard.kyasuka.com
./new-repo.sh pub test "This is a test repository"
exit
{{< /highlight >}}

# Bonus

I had a few repositories in github, so I wrote the following python script to
clone them all into my server.  This will make the transition easier :)

```
cat << EOF > /mnt/disk/git/import-github.py
```
{{< highlight python3 >}}
#! /usr/bin/env python3

from urllib.request import urlopen, urlretrieve
import os, sys, re, subprocess

user = sys.argv[1]
content = urlopen('https://api.github.com/users/%s/repos' % user).read()
content = content.decode('UTF-8')


clone_urls = re.findall('(?<="clone_url":)"[^"]*",', content)
descriptions = re.findall('(?<="description":)(null|"[^"]*"),', content)

descriptions = [d.replace('"', '') for d in descriptions]
os.chdir('pub')
for i in range(0, len(clone_urls)):
    clone_url = clone_urls[i]
    clone_url = clone_url[1:-2]
    print(clone_url)
    subprocess.run(['git', 'clone', '--bare', clone_url])
    with open(clone_url.split('/')[-1] + '/description', 'w') as desc_file:
        desc_file.write(descriptions[i] + '\n')
{{< /highlight >}}
```
EOF
```

And that concludes my initial series of posts on setting up my Raspberry Pi 2 to
act as a git server.  I'm planning on setting up a backup system in the future,
so I may write about it too :)
