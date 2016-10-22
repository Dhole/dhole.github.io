+++
Categories = ["alpine", "raspberry pi", "git"]
date = "2016-10-21T15:14:27-07:00"
draft = true
title = "Raspberry Pi: git server"

+++

```
adduser git
lbu add /home/git/

rmdir /home/git
ln -sf /mnt/disk/git /home/
cp -R /home/green/.ssh /home/git/.ssh
chown -R git:git /home/git/
ln -s /home/git/ /git
```
apk add highlight git cgit

cp /usr/lib/cgit/filters/syntax-highlighting.sh /usr/lib/cgit/filters/syntax-highlighting3.sh

```
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
```

lbu add /usr/lib/cgit/filters/syntax-highlighting3.sh

vim /usr/share/webapps/cgit/cgit-highlight.css

```
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
```

lbu add /usr/share/webapps/cgit/cgit-highlight.css

# We will setup two folders, one for private repos and the other one for public
# repos.
mkdir /etc/cgit

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

```
vim /etc/lighttpd/lighttpd.conf
```

```
...
...
# {{{ includes
...
include "cgit.conf"
...
# }}}
...
...
```

cd /mnt/disk
mkdir -p git/pub
mkdir -p git/priv


lbu commit
rc-service lighttpd start

## git usage

# I'm using the following script to generate empty repositories:


```
cat << EOF > /home/git/new-repo.sh
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
EOF
```

# Now, to create a new git repository I just do the following from my local
# machine:

ssh git@lizard.kyasuka.com
./new-repo.sh pub test "This is a test repository"
exit

# Bonus


```
cat << EOF > /mnt/disk/git/import-github.py
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
EOF
```
