+++
title = "Collapse Ready Operating Systems - FreeBSD"
date = 2025-12-21T00:15:20+02:00
Categories = ["bsd", "freebsd"]
+++

This post belongs to the Collapse Ready Operating System series.  See [this
post](/post/collapse_ready_os) for an introduction.

# Prelude

My last post in this series was more than two years ago.  When I started the
series I had an initial plan to test the three most well known BSD operating
systems, and after publishing articles for NetBSD and OpenBSD I soon
started doing my homework with FreeBSD; unfortunately I had a lot of hiccups.
I've made 4 different attempts at achieving the objectives in this series with
FreeBSD, the last one being last week, and none of them were fully successful.
The reason for trying several times instead of publishing the first result was
to see if some of the issues I encountered were temporary or bugs of a
particular release; but at the end I decided to publish the results I have.

# FreeBSD

In this post I take a look at [FreeBSD](https://www.freebsd.org/).  I used
FreeBSD many years ago in a non-serious server setting.  I think it was the
first BSD I used.  I remember having fun with the port system, but not much
else.  Anecdotically I've also played many hours on the PS4 which runs a
modified version of FreeBSD, so based on that, FreeBSD may be the BSD I've
spent most hours with :P

# Steps

Here I will describe the steps I followed to set up the system and perform the
evaluation.

## Install

I downloaded the install image from
https://download.freebsd.org/releases/amd64/amd64/ISO-IMAGES/15.0/FreeBSD-15.0-RELEASE-amd64-memstick.img
, flashed it to a USB drive and installed it in the main laptop.

I mostly used the default install values:
- keymap: default
- hostname: freebsd
- Installation type: Packages (Tech Preview) which is the default
- Offline (Limited Packages)
- partition: Auto (ZFS)
- system components: include "devel"
- services: default
- hardening options: default (none)
- firmware packages (select none)
    - [ ] gpu-firmware-intel-kmod-kabylake
    - [ ] wifi-firmware-iwlwifi-kmod-8000
- Add user: `user`

Then I rebooted into a the fresh FreeBSD system.

## Setup

By default the user doesn't belong to any extra groups.  We need to be in the
`wheel` group to switch to root via `su`, so let's add our user to the group:
```
pw user mod user -G wheel
```

On a previous attempt I ran out of space in my laptop's NVME disk so I set up a
2TB external hard drive for the ports:
```
zfs umount zroot/usr/ports
zfs destroy zroot/usr/ports

gpart destroy -F da1
gpart create -s GPT da1
zpool create zports /dev/da1
zfs set mountpoint=/usr/ports zports
```

## Ports

I mainly followed the ports documentation at https://docs.freebsd.org/en/books/handbook/ports/

The official documentation requires installing git to fetch the ports, but git
is not part of the base system, so I'd need to install git from binary packages
but the handbook recommends not mixing ports with binary packages, so I want to
try only using ports.  Fortunately the ports repository is in gitlab which
offers tarballs of tagged snapshots.  I'm using the branch 2025Q3.

As root:
```
fetch 'https://gitlab.com/FreeBSD/freebsd-ports/-/archive/2025Q3/freebsd-ports-2025Q3.tar.gz'
tar xf freebsd-ports-2025Q3.tar.gz --strip-components=1 -C /usr/ports/
```

Now we have the ports ready to be used.  I'll first install tmux so that I can
comfortably have a remote persistent session.
```
cd /usr/ports/sysutils/tmux
make BATCH=yes NO_DIALOG=yes DISABLE_LICENSES=yes install
```

One of my goals is to be able to build any port offline.  The port collection I
downloaded only includes the recipes to build the packages but not the source code
(known as distfiles).  I haven't found a specific tool that helps fetching all
the distfiles of all ports so I'll have to use the Makefile rules from the
ports themselves.

I run this command from the ports tree root with the goal of fetching all the
ports' distfiles.
```
make -k BATCH=yes DISABLE_VULNERABILITIES=yes NO_DIALOG=yes DISABLE_LICENSES=yes IGNORE_SILENT=1 fetch
```

The entire process took about 2 days.  One of the reasons why it took so long
is that ports have multiple urls to fetch the distfiles and many of these urls
are not working.  In particular some of them end up with a hanging connection
so the fetch program needs to wait for a timeout to try the next url.  Even
then, many distfiles were not fetched due to non-working urls.

After this we end up with a big collection of distfiles:
```
/usr/ports/distfiles: 520.1 GiB (17860443 items)
```

This is significantly bigger than what I got from NetBSD and OpenBSD.

### Hiccups

Unfortunately the distfiles collection is not complete:
- As I mentioned before, for some ports, none of the urls were working
- In FreeBSD a port can have flavors, which can be used to build different
  version of the port.  In such a case each flavor will have different
  distfiles.  The recursive fetch rule only fetches the distfiles of the
  default flavor.

Moreover, the behavior of the fetch rule is surprising to me: for some ports
not just the disftiles were fetched but actual building happened.  Examples of
this where go (bootstrapping).  Another package which I wasn't able to
determine triggered the build of python39, help2man, meson and other ports.
Overall this happened more times: sometimes a fetch will trigger a chain of
builds.  Not only that but some of these builds end with errors.

Among the errors I found while fetching distfiles was failing to build git,
I'll give more details of the solution later; but I want to point out that
after building git and running the recursive fetch again I ended up with more
distfiles; which again was surprising, I was not expecting a dependency to a
non-base package to fetch a port distfile.

### Testing

After fetching the distfiles I try to build some ports while offline:

I successfully managed to build and install the following ports:
- sysutils/fd
- sysutils/ncdu
- sysutils/htop
- www/gohugo

The last port I wanted to build and install was `x11/xorg` which unfortunately fails:
```
root@freebsd:/usr/ports/x11/xorg # make BATCH=yes NO_DIALOG=yes DISABLE_LICENSES=yes install
===>  Staging for xorg-7.7_3
===>   xorg-7.7_3 depends on file: /usr/local/libdata/pkgconfig/dri.pc - not found
===>   mesa-dri-24.1.7_6 depends on package: py311-ply>0 - found
===>   mesa-dri-24.1.7_6 depends on package: wayland-protocols>=1.8 - found
===>   mesa-dri-24.1.7_6 depends on executable: glslangValidator - found
===>   mesa-dri-24.1.7_6 depends on package: libclc-llvm19>0 - not found
===>   libclc-llvm19-19.1.3 depends on file: /usr/local/sbin/pkg - found
=> libclc-19.1.3.src.tar.xz doesn't seem to exist in /usr/ports/distfiles/.
```
`libclc-19.1.3.src.tar.xz` was not fetched previously.  After checking this
port I see that it supports multiple versions via flavors with version 15 being
the default (and indeed I have the distfile for version 15).

## Building the OS

Information on building the OS: https://wiki.freebsd.org/BuildSystems

Clone the source (https://docs.freebsd.org/en/books/handbook/mirrors/#git) and checkout the release

```
git clone -o freebsd https://git.FreeBSD.org/src.git /usr/src
cd /usr/src
git checkout stable/14
```

https://man.freebsd.org/cgi/man.cgi?query=release&apropos=0&sektion=7&format=html

Now it's time to build without Internet connection:

```
make -j6 buildworld buildkernel
cd release
make -j6 obj
make memstick
```

The memory stick image can be found at `/usr/obj/usr/src/amd64.amd64/release/memstick.img`

I plug a usb memory and via `dmesg` see it's `da1`.  Now I follow https://docs.freebsd.org/en/books/handbook/bsdinstall/#bsdinstall-usb
```
dd if=/usr/obj/usr/src/amd64.amd64/release/memstick.img of=/dev/da1 bs=1M conv=sync
```

Then I successfully managed to install FreeBSD in my thinkpad x220

## Documentation

There's a documentation section about FreeBSD's documentation at
https://docs.freebsd.org/en/books/fdp-primer/

The tools required to build the documentation can be installed via a meta-port: 

```
cd /usr/ports/textproc/docproj
make BATCH=yes install
```

Afterwards we can clone the doc repository using git and build the
html render by following the instructions at
https://docs.freebsd.org/en/books/fdp-primer/doc-build/#doc-build-rendering-html:
```
cd ~
git clone https://git.FreeBSD.org/doc.git

cd ~/doc
make DOC_LANG="en es" # build the documentation in English and Spanish
```

That builds all the doc repository, which includes the FreeBSD website among
other things.  If we just want the documentation (which includes the handbook,
faq and developers-handbook among others):
```
cd `~/doc/documentation`
make DOC_LANG=en
```

# Summary

I would say that FreeBSD didn't pass the collapse-ready test:
- I didn't manage to fetch all the distfiles of the ports collection in a way
  that would allow me to build any port I need without Internet connection.
  Considering that FreeBSD has a massive collection of ports I wouldn't have
  minded not being able to fetch distfiles for unmaintained ports or those that
  have non-free licenses.  But not being able to automatically fetch a distfile
  that is later needed to build xorg was a big issue for me.
- The FreeBSD handbook is pretty good; but the last two operating systems I
  tested were NetBSD and OpenBSD which have superb documentation; I would rank
  the FreeBSD below.  For example, some of the documentation is not in the
  handbook but in the wiki, which is not ideal.  But this can be circumvented
  by cloning the wiki locally, so the only inconvenience is fragmentation and
  worse indexing of content.
- Building the system while offline and creating install media for another
  computer worked great.

# Addendum 

## Failed attempts

### 1

Running `make fetch` in the ports tree gives you a very interactive experience.  I had found a few variables that would make the process more non-interactive by reading the source code of the makefiles and searching online, but then I encountered errors that would stop the process entirely:
```
# make BATCH=yes DISABLE_VULNERABILITIES=yes NO_DIALOG=yes DISABLE_LICENSES=yes fetch
# [...]

=> rarbsd-x64-711.tar.gz doesn't seem to exist in /usr/ports/distfiles/.
=> Attempting to fetch https://www.rarlab.com/rar/rarbsd-x64-711.tar.gz
rarbsd-x64-711.tar.gz                                  737 kB 2660 kBps    00s
===> Fetching all distfiles required by rar-7.11,3 for building
===> archivers/rar-i386
===>  rar-i386-7.01 is only for i386, while you are running amd64 (reason:
amd64 users should use archivers/rar).
*** Error code 1

Stop.
make[2]: stopped in /usr/ports/archivers/rar-i386
*** Error code 1

Stop.
make[1]: stopped in /usr/ports/archivers
*** Error code 1

Stop.
make: stopped in /usr/ports
```

In this case the solution was to add `IGNORE_SILENT=1` so that this build error
is ignored (it's unfortunate that it pops up because I'm not building, just
fetching).

### 2

Even after setting all the variables I could find in the source code that would make the process smooth there are errors.  This one is just an example of a port that has distfiles that are unavailable via the provided urls.
```
make BATCH=yes DISABLE_VULNERABILITIES=yes NO_DIALOG=yes DISABLE_LICENSES=yes IGNORE_SILENT=1 fetch
# [...]

=> phred-dist-020425.c-acd.tar.Z doesn't seem to exist in /usr/ports/distfiles/.
===> /!\ Warning /!\
     The :DEFAULT group used for phred-dist-020425.c-acd.tar.Z is missing
     from MASTER_SITES. Check for typos, or errors.
=> Attempting to fetch http://distcache.FreeBSD.org/ports-distfiles/phred-dist-020425.c-acd.tar.Z
fetch: http://distcache.FreeBSD.org/ports-distfiles/phred-dist-020425.c-acd.tar.Z: Not Found
=> Couldn't fetch it - please try to retrieve this
=> port manually into /usr/ports/distfiles/ and try again.
*** Error code 1

Stop.
make[2]: stopped in /usr/ports/biology/phred
*** Error code 1
```

The solution is to pass `-k` to `make`, which makes it continue even if errors
are found on some rule.
