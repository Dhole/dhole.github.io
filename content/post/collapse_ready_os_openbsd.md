+++
title = "Collapse Ready Operating Systems - OpenBSD"
date = 2023-02-21T00:15:20+02:00
Categories = ["bsd", "openbsd"]
+++

This is a blog post in the Collapse Ready Operating System series.  Read [this
post](/post/collapse_ready_os) for an introduction.

# OpenBSD

The OS analyzed in this post is [OpenBSD](https://www.openbsd.org/).  I've
tried OpenBSD a few times in the past: once as a personal web server on an old
PC, and then as a desktop in a laptop as a secondary system.  That was a few
years ago.  My memories from it are that the system was very clean, everything
worked as expected, the performance was significantly slower than linux and
that I really appreciated all the care the developers put on the security side.

# Steps

In the following sections I describe all the steps I followed to setup up the
system and evaluate it.

## Install

Download install image from the website:
https://cdn.openbsd.org/pub/OpenBSD/7.2/amd64/install72.img (This is OpenBSD
7.2, the latest release at the time, for amd64). Then write it to a flash drive
and boot from the main laptop.

Follow the install instructions (pretty simple).

I followed mostly the defaults, setting up the em0 (ethernet) net interface as
'autoconf', then using the whole disk in the auto layout paritioning.  I created a
user named `user`.  Install all sets.  Enable xenodm on startup.

To pick the install sets from the disk answer the following questions like
this:
- `Location of sets? 'disk'`
- `Is the disk partition already mounted? 'no'`
- `Which disk contains the install media? 'sd1'` (this may change in your setup,
  you should choose the drive with the install image)
- `Which sd1 partition has the install sets? 'a'`
- `Pathname to the sets? '7.2/amd64'`
- `Directory does not contain SHA256.sig. Continue without verification? 'yes'`

Afterwards reboot and login as `user`.

## Basic setup

Enable `doas` for my user (without password) for convenience:
```
su -l
echo "permit nopass :wheel" > /etc/doas.conf
```

Install some basic packages as root:
```
doas pkg_add vim--no_x11 wget
```

I decided to use an external 2TB drive for the ports.  Upon connecting the
drive i checked dmesg to see its name:
```
sd2 at scsibus5 targ 1 lun 0: <TOSHIBA, External USB 3.0, 5438> serial.0480021070803005453F
sd2: 1907729MB, 512 bytes/sector, 3907029164 sectors
```

Then I formated it following the docs at https://www.openbsd.org/faq/faq14.html
```
doas newfs sd2i
```

And then I mount it at `/mnt/disk`:
```
doas mkdir -p /mnt/disk
doas mount -o wxallowed /dev/sd2i /mnt/disk/
doas chown user /mnt/disk
```

Add my user to the `wsrc` group (this will allow building the ports as a regular user):
```
doas user mod -G wsrc user
```

For the group change to take effect you must logout and login again.

## Fetching the system sources and ports

OpenBSD has its source code split into two parts: `src` and `xenocara`.  `src`
contains the kernel as well as all system userland.  `xenocara` contains the
X11 fork used by OpenBSD.  These will give you a base OpenBSD, which is already
useful as it contains many utilities and programs.

Third party software is offered via `ports`.  These are recipes to build a big
library of open source packages.  The recommended way to install packages by
OpenBSD is to use `pkg_add` which fetches the already built package from an
OpenBSD mirror.  For my usecase I would like to keep all the package sources
locally to build port offline later.

Download the OpenBSD source as well as ports recipes for the 'release' flavor.
I followed the instructions in https://www.openbsd.org/faq/ports/ports.html

```
cd /mnt/disk
ftp https://cdn.openbsd.org/pub/OpenBSD/$(uname -r)/{ports.tar.gz,src.tar.gz,sys.tar.gz,xenocara.tar.gz,SHA256.sig}
signify -Cp /etc/signify/openbsd-$(uname -r | cut -c 1,3)-base.pub -x SHA256.sig ports.tar.gz src.tar.gz sys.tar.gz xenocara.tar.gz

cd /usr
doas mkdir -p xenocara ports src
doas chown user xenocara ports src
doas chgrp wsrc xenocara ports src
doas chmod 775  xenocara ports src

cd /usr && tar xzf /mnt/disk/ports.tar.gz
cd /usr/src && tar xzf /mnt/disk/src.tar.gz
cd /usr/src && tar xzf /mnt/disk/sys.tar.gz
cd /usr/xenocara && tar xzf /mnt/disk/xenocara.tar.gz
```

Summary
- `/usr/src` 1.4 GiB 132505 items
- `/usr/xenocara` 726.5 MiB 37101 items
- `/usr/ports` 726 MiB 229896 items

### Firmware

OpenBSD uses firmware packages to support some hardware components.  These
firmwares contain blobs that can't be distributed with the OpenBSD license, so
they are instead offered via http, and installed during the first boot (with
Internet connection).

Download all the firmwares files for offline usage.
```
cd /mnt/disk/
wget --execute="robots = off" --mirror --convert-links --no-parent http://firmware.openbsd.org/firmware/$(uname -r)/
cd firmware.openbsd.org/firmware/$(uname -r)/
signify -Cp /etc/signify/openbsd-$(uname -r | cut -c 1,3)-fw.pub -x SHA256.sig *.tgz
```

### Documentation

OpenBSD has excelent man pages for its internal programs and configuration
files (which are installed in the system so they can be accessed offline).  But
I also found the FAQ extremely well written and very useful.  I used it
extensively during this project.  The FAQ is not found in the installation or
in any package, but the entire website is available via CVS, so fetching a copy
for offline reading is very easy:
```
cd /usr
doas mkdir -p www
doas chgrp wsrc www
doas chmod 775 www
SERVER="anoncvs.fr.openbsd.org"
cvs -qd anoncvs@$SERVER:/cvs checkout -rHEAD -P www
```

These are some browsers that I installed to read the FAQ: `www/w3m`,
`www/dillo`, `www/links+`.

Note that `dillo` requires `env FORCE_UNSAFE_CONFIGURE=1 make install` to be built as root.

The three browsers work perfectly for reading the OpenBSD FAQ:
```
# w3m (console)
w3m /usr/www/index.html
# links+ (console)
links /usr/www/index.html
# links+ (gui)
links -g /usr/www/index.html
# dillo (graphical)
dillo /usr/www/index.html
```

## Ports

I want to use my external disk for port related files (except for the port recipes themselves): 
```
mkdir -p /mnt/disk/ports
```

Write these contents into `/etc/mk.conf`:
```
WRKOBJDIR=/mnt/disk/ports/pobj
DISTDIR=/mnt/disk/ports/distfiles
PACKAGE_REPOSITORY=/mnt/disk/ports/packages
```

At this point we have all the sources to build the OS and the recipes to build
all ports.  Nevertheless on the ports side this doesn't include the packages'
sources, which I would like to have.  Right now we could build a port, and
the required package sources would be fetched from the Internet; but I would
like to have them available on disk to build any port offline.

Luckily, while reading the documentation page about Ports at
https://www.openbsd.org/faq/ports/ports.html I found that OpenBSD has the `dpb`
tool.  This tool was made to automate building ports to later on distribute the
packages.  In my case I'm interested in the feature to fetch all the distfiles.
Here's the man: https://man.openbsd.org/dpb

Download all ports distfiles (source code required for building the ports):
```
doas /usr/ports/infrastructure/bin/dpb -F 12
```

I left this program running all night and came back and saw it got stuck with this output:
```
5 Feb 11:37:50 [64941] control-laptop-64941 elapsed: 10:36:32
<freeipmi-1.6.10.tar.gz(#1) [84727] 11% frozen for 9 HOURS!
Hosts: localhost
I=0 B=0 Q=2888 T=8230 F=0 !=8
E=security/libdigidocpp:libdigidocpp/iconv-470.patch
```

I stopped it and started it again, and this second time it ended cleanly (and
quickly).  The man page mentions a bug, which may be this one:
> When fetching distfiles, dpb may freeze and spin in a tight loop while the
> last distfiles are being fetched. This is definitely a bug, which has been
> around for quite some time, which is a bit difficult to reproduce, and hasn't
> been fixed yet. So if dpb stops updating its display right around the end of
> fetch, you've hit the bug. Just kill dpb and restart it.

Summary:
- `/mnt/disk/ports/distfiles` 75.7 GiB 98533 items

Now we have all the files necessary to build any package.

Let's try it!  Without Internet connection of course.

The first port we install will give us a database of ports so that we can
search them for convenience.  The package is `portslist`.  This port contains 2
subpackages, so we use `install-all` to install all of them, otherwise only the
main package `sqlports` is installed.
```
cd /usr/ports/databases/sqlports
doas make install-all
```

Now we search for some packages and build & install them
```
cd /usr/ports
make search key=fd # From this we know where to find the package

cd sysutils/fd
doas make install

cd /usr/ports/editors/neovim
doas make install
```

## Building the system

Following https://www.openbsd.org/faq/faq5.html which points me to the man for `release(8)`:
```
su -l

# 2. Build kernel
cd /sys/arch/$(machine)/compile/GENERIC.MP
make obj && make config && make

# 3. BUild base system
cd /usr/src
make obj && make build

# 4. Make and validate the base system release
mkdir /var/releasedir
chown build /var/releasedir
mkdir /var/mfs
mount_mfs -o rw,noperm -s 2G swap /var/mfs
chown build /var/mfs
chmod 700 /var/mfs
mkdir /var/mfs/destdir
export DESTDIR=/var/mfs/destdir RELEASEDIR=/var/releasedir
cd /usr/src/etc && make release
cd /usr/src/distrib/sets && sh checkflist
unset RELEASEDIR DESTDIR

# 5. Build Xenocara
cd /usr/xenocara
make bootstrap && make obj && make build

# 6. make and validate the Xenocara release
mkdir /var/mfs/xenocara-destdir
export DESTDIR=/var/mfs/xenocara-destdir RELEASEDIR=/var/releasedir
make release && make checkdist
unset RELEASEDIR DESTDIR

# 8. Create boot and installation disk images
export RELDIR=/var/releasedir RELXDIR=/var/releasedir
cd /usr/src/distrib/$(machine)/iso && make
make install
```

Summary:
- `/usr/obj` 5.3 GiB 59435 items
- `/usr/xobj` 1.5 GiB 19536 items
- `/var/releasedir` 1.7 GiB 24 items

Now the install images are ready in `/var/releasedir`

Let's flash the installer to a usb drive and test it on another laptop
```
cd /var/releasedir/
# My usb drive device is sd3, as seen from dmesg
dd if=install72.img of=/dev/rsd3c bs=1M
```

Let's copy the firmware files into the drive as well
```
mkdir /mnt/install
mount sd3a /mnt/install/
cp -r /mnt/disk/firmware.openbsd.org/firmware /mnt/install/
umount /mnt/install
```

After this we have recreated an install image and flashed it into a usb drive
that we can use to install the system in another laptop.  The installation can
be done as usual.  To install the firmware files we can use the same install
usb drive in the new system:
```
su -l
mkdir /mnt/install
# My usb drive device is sd2 here, as seen from dmesg
mount /dev/sd2a /mnt/install
fw_update -p /mnt/install/firmware/7.2
```

And with this the cycle is complete :D

# Summary

OpenBSD passed the test!  I was able to achieve the 4 evaluation objectives
described in the Introduction.  I also found the documentation (both in man
pages and FAQ) to be excelent.  I was able to follow all the procedures
described in this post using just that (instead of relying on forums or other
Internet content).  This is fantastic because in an offline scenario these
resources would be in the laptop, giving OpenBSD more points for
collapse-readiness.

# Addendum 

## Failed attempts

### Failure number 1

In `/usr/ports/sysutils/fd` I originally did `doas make install -j4` thinking
that it would run 4 make jobs in parallel.  After a while I got an error
complaining that a dependency port couldn't be compiled.  I found out that
support for parallel makes in the ports is not well supported (from the man
page), so I continued without the `-j4`.

Seen in man for `bsd.port.mk`:
```
MAKE_JOBS
    Number of jobs to use when building the port, normally passed to MAKE_PROGRAM through PARALLEL_MAKE_FLAGS. Mostly set automatically when DPB_PROPERTIES contains ‘parallel’.

    Note that make(1) still has bugs that may prevent parallel build from working correctly!
```

I continued the process without using `-j4` on `make` again.  Some build times
have been a bit slow (partily due to using a single core).

### Failure number 2

In `/usr/ports/sysutils/fd` some time after I ran `doas make install` I got the following error:
```
Fatal: /usr/ports/pobj must be on a wxallowed filesystem (in lang/ruby/3.1)
*** Error 1 in /usr/ports/lang/ruby/3.1 (/usr/ports/infrastructure/mk/bsd.port.mk:2865 '_post-patch-finalize': @wrktmp=`df -P /usr/ports/pob...)
```

I didn't find any mention of this in the documentation, I guess this is a
specific detail of a particular port.  In OpenBSD's defense, they claim that
the supported way to install packages is with `pkg_add`, so it's fair that
making ports requires some small troubleshooting.

The solution for this is very easy: mount `/mnt/disk` (where I have the ports
object directory) as `wxallowed`.

### Failure number 3

Third attemp to build `fd`.  At some point `fd` requires building `ruby` as a dependency (I guess build dependency), and it fails with:

```
===>  Building package for ruby-3.1.3
Create /usr/ports/packages/amd64/all/ruby-3.1.3.tgz
Creating package ruby-3.1.3
checksumming|*                                                                                     | 1%
Error: /usr/ports/pobj/ruby-3.1.3/fake-amd64/usr/local/bin/bundle31 does not exist
Error: /usr/ports/pobj/ruby-3.1.3/fake-amd64/usr/local/bin/bundler31 does not exis
Error: /usr/ports/pobj/ruby-3.1.3/fake-amd64/usr/local/bin/erb31 does not exist
Error: /usr/ports/pobj/ruby-3.1.3/fake-amd64/usr/local/bin/irb31 does not exist
Error: /usr/ports/pobj/ruby-3.1.3/fake-amd64/usr/local/bin/racc31 does not exist
Error: /usr/ports/pobj/ruby-3.1.3/fake-amd64/usr/local/bin/rdoc31 does not exist
Error: /usr/ports/pobj/ruby-3.1.3/fake-amd64/usr/local/bin/ri31 does not exist
Error: /usr/ports/pobj/ruby-3.1.3/fake-amd64/usr/local/lib/ruby/gems/3.1/gems/bundler-2.3.26/libexec/bundle does not exist
Error: /usr/ports/pobj/ruby-3.1.3/fake-amd64/usr/local/lib/ruby/gems/3.1/gems/bundler-2.3.26/libexec/bundler does not exist
Error: /usr/ports/pobj/ruby-3.1.3/fake-amd64/usr/local/lib/ruby/gems/3.1/gems/erb-2.2.3/libexec/erb does not exist
```

This took me the longest to debug, and it was a bug in ruby.

I reproduced all the steps in a vm (without fetching all the distfiles, and not
using any external disk) up to building `ruby/3.1`.  And in that scenario it built
successfully.  There must be some detail in my setup that breaks the `ruby`
build.

Originally I was using the external drive for the ports related files mounted
at `/mnt/ext`.  For that I had set `WRKOBJDIR=/mnt/ext/ports/pobj` in
`/etc/mk.conf`.
After retrying several times (removing a difference between my setup and the vm
setup each time) I tried removing the line with `WRKOBJDIR` from `/etc/mk.conf`
and then the building worked correctly.  Then I explored different `WRKOBJDIR` (same
filesystem, changing filesystem, etc.), and from this I found out that I only got the
error when the `WRKOBJDIR` contains a `/ext/` in it (remember I had my external
drive mounted at `/mnt/ext`).  By analyzing the logs between success and error
scenario I found that these two output lines in the error case showed that no
gems had been found:
```
installing default gems from lib:   /usr/local/lib/ruby/gems/3.1
installing default gems from ext:   /usr/local/lib/ruby/gems/3.1
```

Whereas in the successful case a list of gems had been found, which were the
ones that later were not found when trying to build the package in the failing
case.

So I started looking at the code in ruby (by searching for strings that
contained "installing default gems from lib:")... and I finally found the
issue.  In `tool/rbinstall.rb` at some point gems are listed and a check is run
to determine if they should be skipped.  This is the relevant snippet:
```ruby
      def skip_install?(files)
        case type
        when "ext"
          # install ext only when it's configured
          !File.exist?("#{$ext_build_dir}/#{relative_base}/Makefile")
        when "lib"
          files.empty?
        end
      end

      private
      def type
        /\/(ext|lib)?\/.*?\z/ =~ @base_dir
        $1
      end
```

The problem appears in the `type` function which applies a regex to the gemspec
dir.  For example, in my setup it would be
`/mnt/ext/ports_pobj2/ruby-3.1.2/ruby-3.1.2/lib/bundler/`, and instead of
returning `lib` (which is the expected result) it would return `ext` by
matching at `/mnt/ext/...`.  That causes the script to check for the existence
of a file that isn't there, so the gem is skipped.

So the conclusion is that the build path for Ruby must not contain directories
named `ext` or `lib`.

I checked Ruby 3.2.0 and the logic to handle "ext"/"lib" has been reworked to
avoid this problem :)  So I guess there's nothing to report!
