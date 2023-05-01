+++
title = "Collapse Ready Operating Systems - NetBSD"
date = 2023-05-01T12:00:20+02:00
Categories = ["bsd", "netbsd"]
+++

This is a blog post in the Collapse Ready Operating System series.  Read [this
post](/post/collapse_ready_os) for an introduction.

# NetBSD

This time I have chosen [NetBSD](https://netbsd.org).  I have used NetBSD previously in my Raspberry Pi (the first version).  I had a lot of fun building packages for ARM from the raspberry pi and trying them out (and finding bugs as well).  I remember fondly the regular [status reports](https://mail-index.netbsd.org/port-arm/2022/10/26/msg007897.html) made by Jun Ebihara along with raspberry pi images with many packages already installed.  I also remember building a raspberry pi image myself from a Linux host on amd64 using cross-compilation: I was quite impressed with how easy the process was.

# Steps

In the following sections I describe all the steps I followed to setup up the
system and evaluate it.

## Install

Download the install image from https://cdn.netbsd.org/pub/NetBSD/NetBSD-9.3/images/NetBSD-9.3-amd64-install.img.gz which is the installer of NetBSD 9.3 for amd64.  Write it to a flash drive and boot from it in the main laptop.

After boot, follow the steps to perform a NetBSD installation.  Use the whole disk with default partition sizes.
Choose "Full installation" in the "Select your distribution" step.
At the "Install from" step, choose first option: "... install image media", so
that the resources are retrieved from the install usb disk.

In the configuration steps, make these choices:
- Configure network -> `wm0` with autoselect
- Timezone -> `Europe/Madrid`
- Change root password -> `toor`
- Enable sshd -> YES
- Enable xdm -> YES
- Add a user -> `user:password` and choose to add it to the wheel group.  Set default shell to `/bin/ksh` to get autocompletion

Reboot into the system and login as `user`.

## Basic setup

I found out that the recommended way to install packages is to use `pkgin` which is not installed by default, so let's install it.  Following the pkgsrc website quickstart section at https://pkgsrc.org/:
```
PKG_PATH="http://cdn.NetBSD.org/pub/pkgsrc/packages/NetBSD/$(uname -p)/$(uname -r|cut -f '1 2' -d.)/All/"
export PKG_PATH
pkg_add pkgin
```

This succeeds with the following warnings:
```
pkg_add: Warning: package `pkgin-21.12.0nb2' was built for a platform:
pkg_add: NetBSD/x86_64 9.0 (pkg) vs. NetBSD/x86_64 9.3 (this host)
pkg_add: Warning: package `pkg_install-20211115' was built for a platform:
pkg_add: NetBSD/x86_64 9.0 (pkg) vs. NetBSD/x86_64 9.3 (this host)
```

Nevertheless the NetBSD wiki says this is normal https://wiki.netbsd.org/pkgsrc/faq/

Install some basic software as root:
```
pkgin install vim doas wget
```

Configure `doas` to run commands as root from our user (which belongs to the `wheel` group):
```
echo "permit nopass :wheel" > /usr/pkg/etc/doas.conf
```

I will use an external 2TB drive to download the distribution files to build packages.
Note: NetBSD uses the term `package` to refer to the same thing that FreeBSD and OpenBSD call `port`.

Following the documentation from https://www.netbsd.org/docs/guide/en/chap-misc.html#chap-misc-adding-new-disk
First plug the disk and see via `dmesg` the device name:
```
[Sun Feb 19 14:27:02 CET 2023] sd1 at scsibus1 target 0 lun 0: <TOSHIBA, External USB 3.0, 5438> disk fixed
```

Then format it and mount it
```
doas newfs /dev/rsd1i
doas mkdir /mnt/disk
doas mount /dev/sd1i /mnt/disk
doas chown user /mnt/disk
```

### pkgsrc

pkgsrc is the framework that NetBSD uses to build packages from source.  pkgsrc
extends beyond NetBSD: it supports multiple Unix-like operating systems such as
Linux.

Follow instructions from https://netbsd.org/docs/pkgsrc/getting.html and the
sections that follow.

pkgsrc publishes quarterly releases: download and extract the latest one:
```
cd /mnt/disk
ftp https://cdn.netbsd.org/pub/pkgsrc/pkgsrc-2022Q4/pkgsrc.tar.gz
doas tar -xzf pkgsrc.tar.gz -C /usr
```

Summary:
- `/usr/pkgsrc/` 1.3G

Then run the bootstrap script to build and install all the dependencies
required to build packages:
```
cd /usr/pkgsrc/bootstrap/
doas ./bootstrap
```

We set the path for the `distfiles` (the files with the source code and assets
require to build the packages) to point to the external disk.
For that, edit our `mk.conf`:
```
mkdir -p /mnt/disk/pkgsrc/distfiles
doas vim /usr/pkg/etc/mk.conf
# Add this line before the `.endif`
DISTDIR=/mnt/disk/pkgsrc/distfiles
```

Now let's fetch all the `distfiles`:
```
# This took ~2h
MASTER_SORT_RANDOM=NO MASTER_SORT_REGEX='http://cdn.NetBSD.org/.*' bmake fetch-list > /mnt/disk/fetch-all.sh
cd /mnt/disk/pkgsrc/distfiles
time sh /mnt/disk/fetch-all.sh
```

This fetches the distfiles for each package by choosing the http://cdn.NetBSD.org/ mirror whenever it's available.

Summary:
- /mnt/disk/pkgsrc/distfiles 67G

Now let's try to build something without Internet connection:
```
su -l
cd /usr/pkgsrc/sysutils/htop/
MAKE_JOBS=4 bmake install
cd /usr/pkgsrc/sysutils/ncdu/
MAKE_JOBS=4 bmake install
cd /usr/pkgsrc/sysutils/fd-find/
MAKE_JOBS=4 bmake install
```

With `MAKE_JOBS=4` the builds are quite fast.  Reading `mk/defaults/mk.conf` I
see that some packages don't work with parallel jobs; I expect that if I
encounter such a package the building will fail and I can retry without this
env var set.

## Building the system

Following the documentation at https://www.netbsd.org/docs/guide/en/part-compile.html

```
doas mkdir /usr/src
doas chown user /usr/src
doas mkdir /usr/xsrc
doas chown user /usr/xsrc

cd /mnt/disk
for file in gnusrc.tgz sharesrc.tgz src.tgz syssrc.tgz xsrc.tgz; do wget https://ftp.NetBSD.org/pub/NetBSD/NetBSD-9.3/source/sets/$file; done
for file in gnusrc.tgz sharesrc.tgz src.tgz syssrc.tgz xsrc.tgz; do tar -xzf $file -C /; done
```

Summary:
- /usr/src 2.8 GiB 307923 items
- /usr/xsrc 905 GiB 50223 items

The install image can be built with a single command, which is really
convenient.  It also supports parallel jobs, leading to shorter build times.
```
mkdir /mnt/disk/obj
cd /usr/src
./build.sh -U -u -x -j6 -O /mnt/disk/obj tools release install-image
```

That took 2h 30m

Now we can flash the install image to a usb drive and test it on another
laptop.  The installation can be done as usual.
```
cd /mnt/disk/obj/releasedir/images/
gunzip NetBSD-9.3-amd64-install.img.gz
# My usb drive device is sd2, as seen from dmesg
dd if=NetBSD-9.3-amd64-install.img ibs=1m | doas progress dd of=/dev/rsd2 obs=1m
```

With that, the cycle is complete!

# Documentation

NetBSD has an extensive documentation on its website.  I mostly followed such
documentation to write this post.  Luckily the web documentation is stored in
cvs and so it's easy to download.  The documentation even contains a section on
how to mirror the NetBSD website which I followed at https://www.netbsd.org/docs/mirror.html#www-retrieve:

```
cd /usr
doas mkdir -p htdocs
doas chgrp wheel htdocs
doas chmod 775 htdocs
cvs -qd anoncvs@anoncvs.NetBSD.org:/cvsroot checkout -rHEAD -P htdocs
cd htdocs
wget -nv -xnH -NFi mirrors/fetch.html
```

Summary:
- /usr/htdocs 326 MiB 7900 items

These are some browsers to install: `www/w3m`, `www/dillo`, `www/links-gui`.
They are suitable to browse the local html documentation.

The three browsers work perfectly:
```
# w3m (console)
w3m /usr/htdocs/docs/index.html
# links+ (console)
links /usr/htdocs/docs/index.html
# links+ (gui)
links -g /usr/htdocs/docs/index.html
# dillo (graphical)
dillo /usr/htdocs/docs/index.html
```

# Summary

NetBSD passes the test!  I successfully achieved the 4 goals described in the
introduction post.  There were some hiccups during the process that I found
were not addressed by the documentation, but I managed to make progress until
reaching the goal.  I found the task to build the install image very smooth
and straight forward, with basically a single command to build the whole system
and prepare the install image!  The website documentation has been very
helpful.  Since that documentation is easy to copy for offline usage, NetBSD
would be a very good candidate for a collapse-ready operating system.

# Addendum

## Failed attempts

### Failure number 1

When installing `pkgin`, which is the recommended way to install packages, I
originally followed the documentation at
https://netbsd.org/docs/pkgsrc/using.html#installing-binary-packages which
tells us to do the following:
```
su -l
PATH="/usr/pkg/sbin:/usr/pkg/bin:$PATH"
PKG_PATH="https://cdn.NetBSD.org/pub/pkgsrc/packages"
PKG_PATH="$PKG_PATH/NetBSD/amd64/9.3/All/"
export PATH PKG_PATH
pkg_add pkgin
```

This gives me the following error:
```
pkg_add: Can't process https://cdn.netbsd.org:443/pub/pkgsrc/packages/NetBSD/x86_64/9.3/All/pkgin*: Unknown HTTP error
pkg_add: no pkg found for 'pkgin', sorry.
pkg_add: 1 package addition failed
```

The `afterboot` man page gives similar commands:
```
export PKG_PATH=https://cdn.netbsd.org/pub/pkgsrc/packages/NetBSD/$(uname -p)/$(uname -r | cut -d_ -f1)/All
pkg_add pkgin
```
which return the same error.

It seems that the previous error was coming because the `PKG_PATH` is an https
url.  Maybe the TLS CA certificates are not installed and thus a verified https
connection cannot be established?  I tried installing the TLS CA certificates
tu rule out this case!  Maybe `pkg_add` doesn't support https at all?  It feels
strange that the process to install the recommended package manager by NetBSD
involves downloading a binary over http that we will use later, as root.

Changing the url to use `http` works.  So I observe that on a fresh install,
`pkg_add` doesn't support https.  I had to install `pkgin` via `http`.  This
makes me feel a bit uncomfortable because I don't know if there's any signature
check before installing the downloaded package which is downloaded via an
unencrypted and unauthenticated channel. 

### Failure number 2


Now let's fetch all the `distfiles`:
```
# This took ~2h
bmake fetch-list > /mnt/disk/fetch-all.sh
cd /mnt/disk/pkgsrc/distfiles
time sh /mnt/disk/fetch-all.sh
```

This `fetch-list` function of pkgsrc generates scripts to fetch the distfiles
for each package by choosing one of the available mirrors (per package) at
random.  Some of the mirrors were quite slow, giving download speeds of ~20
KiB/s.

After more than 8h running the script it hadn't finished, probably due to slow
mirrors.  So I decide to cancel this and try a different approach.

```
MASTER_SORT_RANDOM=NO MASTER_SORT_REGEX='http://cdn.NetBSD.org/.*' bmake fetch-list > /mnt/disk/fetch-all.sh
```

Running the script now was a bit faster, it took nearly 13h.  It still took a
long time.  Fetching from `cdn.NetBSD.org` gave a speed of ~2 MiB/s.  For
some distfiles the NetBSD cdn gave 404 so the fallback was some ftp server,
which gave speeds of ~20 KiB/s.  I tried downloading from both resources on a
Linux PC and the speed was much higher (both cdn and ftp servers).  My laptop
is connected via Ethernet.  I don't know the reason for the slow download
speeds.

I tested downloading with `wget` and the speeds are much faster.  So using
`wget` with the `fetch-list` can help getting lower download times. I checked
the man page for `ftp` to see if there was some configuration that may make it
run slow, and I've discovered that changing the socket buffer sizes makes a big
difference.  For example, with normal `ftp` I get 3 MiB/s, but with `ftp -x
131072` I get 11.5 MiB/s.
