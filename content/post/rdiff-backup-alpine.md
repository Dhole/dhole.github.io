+++
Categories = ["alpine", "rdiff-backup"]
date = "2016-11-01T01:17:17-07:00"
title = "rdiff-backup-1.2.8 in Alpine"

+++

# Introduction

A few days ago I wanted to start doing incremental backups from my laptop to my
Raspberry Pi 2 running Alpine Linux.  I've had used rdiff-backup for some years
now and I'm really happy with it.  rdiff-backup is similar to rsync, in the
sense that lets you synchronize folders over the network, but it has two added
nice features: when synchronizing, only the differences between the files that
have changed are sent; and after every synchronization, the differences between
the old version of the files and the new ones is kept.  In other words, it keeps
backwards in time incremental backups, allowing you to revert the files in time.

After trying to backup my Documents folder from my Debian laptop I encountered
an error that was caused by an incompatibility between versions.  [Debian
packages version 1.2.8](https://packages.debian.org/jessie/rdiff-backup) while
[Alpine packages version
1.3.3](https://pkgs.alpinelinux.org/packages?name=rdiff-backup&branch=&repo=&arch=&maintainer=).
I found this to be an odd decision for Alpine.  [Both versions were released in
March 2009](http://www.nongnu.org/rdiff-backup/) and haven't had any update
since then.  Version 1.2.8 is marked as stable whereas 1.3.3 is marked as
development/unstable.  I don't know the internal differences between the two
versions, but I checked other distributions like
[Arch](https://www.archlinux.org/packages/?q=rdiff-backup) and they also package
version 1.2.8 instead of 1.3.3.

So, in order to get the version 1.2.8 in Alpine I took the easy route and
installed it manually.  After having done this, I realize that maybe it would
have been much better to learn about the Alpine build system and build the
package by reverting the [commit that updated rdiff-backup from 1.2.8 to
1.3.3](http://git.alpinelinux.org/cgit/aports/commit/main/rdiff-backup/APKBUILD?id=b633874f5c8b490cbd371338f7fb7b8f649ca009)

# Build and install

Anyhow, here's how I installed rdiff-backup 1.2.8 manually:

We first install rdiff-backup dependencies plus the packages required to build
rdiff-backup from source.
```
apk add librsync
apk add gcc librsync-dev python-dev musl-dev patch
```

We download the sources of rdiff-backup-1.2.8, check the hash sum to verify that
we got it right and we extract them.
```
mkdir tmp
cd tmp/
wget http://savannah.nongnu.org/download/rdiff-backup/rdiff-backup-1.2.8.tar.gz
[ "0d91a85b40949116fa8aaf15da165c34a2d15449b3cbe01c8026391310ac95db" \
    = $(sha256sum rdiff-backup-1.2.8.tar.gz | cut -d " " -f 1) ] && echo OK
tar xzf rdiff-backup-1.2.8.tar.gz
```

Then we download the required patch to build rdiff-backup with librsync-1.0.0,
in this case, from the Arch package git repository.  We check the patch and
apply it.
```
wget https://git.archlinux.org/svntogit/community.git/plain/trunk/rdiff-backup-1.2.8-librsync-1.0.0.patch?h=packages/rdiff-backup \
    -O rdiff-backup-1.2.8-librsync-1.0.0.patch
[ "a00d993d5ffea32d58a73078fa20c90c1c1c6daa0587690cec0e3da43877bf12" \
    = $(sha256sum rdiff-backup-1.2.8-librsync-1.0.0.patch | cut -d " " -f 1) ] && echo OK
cd rdiff-backup-1.2.8/
patch -Np1 -i ../rdiff-backup-1.2.8-librsync-1.0.0.patch
```

We are ready to build rdiff-backup and install it in the system.
```
python setup.py build
python setup.py install --prefix=/usr --root=/
```

We must not forget to add the newly installed files in the local backup
database, so that they are stored permanently.  I deliberately skip the docs.
```
lbu add /usr/lib/python2.7/site-packages/rdiff_backup* /usr/bin/rdiff-backup*
```

After we are done, we can remove the packages we used to build rdiff-backup.
```
apk del gcc librsync-dev python-dev musl-dev patch
```

Now rdiff-backup works correctly from my Debian laptop to my Alpine Raspberry Pi
:)
