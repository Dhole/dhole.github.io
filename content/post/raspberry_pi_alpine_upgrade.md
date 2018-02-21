---
Categories: ["alpine", "raspberry pi"]
title: "Alpine Linux: Upgrading on Raspberry Pi"
date: 2017-06-26T23:18:39-07:00
---

This post describes the upgrade procedure I follow to upgrade my Raspberry Pi
Alpine Linux installation.  Alpine Linux on the Raspberry Pi runs from ramfs
and thus the upgrading is not straightforward.  Most of the details are taken
from the [Alpine Linux
Wiki](https://wiki.alpinelinux.org/wiki/Upgrading_Alpine#Upgrading_to_latest_release).
I'm not sure if Alpine Linux does any verification on the new downloaded
release, so I'm doing that manually on another computer.


# Upgrading

First of all, replace the repository confiration to point to the new version:

{{< highlight bash >}}
setup-apkrepos
{{< /highlight >}}

Press `e` then replace v3.5 by v3.6 (or whichever is the new release version).

{{< highlight bash >}}
apk update
apk upgrade --update-cache --available
{{< /highlight >}}

Make sure that `/etc/lbu/lbu.conf` has the following line:

{{< highlight bash >}}
LBU_MEDIA=mmcblk0p1
{{< /highlight >}}

Then load the environment variables from the file, and backup everything.

{{< highlight bash >}}
. /etc/lbu/lbu.conf
lbu ci
{{< /highlight >}}

Check that there is at least 400MB (maybe more?) free in the permament storage:

{{< highlight bash >}}
df -h | grep "Filesystem\|$LBU_MEDIA"
{{< /highlight >}}

Now on another computer, which should have the Alpine Linux release GPG keys on
the GPG keyring, download the new release image, verify it's hash and verify
the hash signature:

{{< highlight bash >}}
VERSION=3.6.2
wget http://dl-3.alpinelinux.org/alpine/latest-stable/releases/armhf/alpine-rpi-$VERSION-armhf.tar.gz
wget http://dl-3.alpinelinux.org/alpine/latest-stable/releases/armhf/alpine-rpi-$VERSION-armhf.tar.gz.asc
wget http://dl-3.alpinelinux.org/alpine/latest-stable/releases/armhf/alpine-rpi-$VERSION-armhf.tar.gz.sha256

sha256sum *armhf.tar.gz
cat *armhf.tar.gz.sha256
gpg --verify *armhf.tar.gz.asc
{{< /highlight >}}

Now we proceed with the upgrade on the Raspberry Pi:

{{< highlight bash >}}
mount -oremount,rw /media/$LBU_MEDIA
cd /media/$LBU_MEDIA
{{< /highlight >}}

Download the new release image (this time on the Raspberry Pi) and verify that
the hash matches the one we verified on the other computer, then extract it:

{{< highlight bash >}}
VERSION=3.6.2
wget http://dl-3.alpinelinux.org/alpine/latest-stable/releases/armhf/alpine-rpi-$VERSION-armhf.tar.gz
sha256sum *armhf.tar.gz
mkdir new 
cd new 
tar xzf ../alpine-rpi-$VERSION-armhf.tar.gz
cd ..
{{< /highlight >}}

Commented is the line suggested in the wiki, which I'm not sure does any
verification.  We will install from the extracted release image:

{{< highlight bash >}}
#setup-bootable -u http://dl-3.alpinelinux.org/alpine/latest-stable/releases/armhf/alpine-rpi-$VERSION-armhf.tar.gz /media/$LBU_MEDIA
setup-bootable -u /media/$LBU_MEDIA/new /media/$LBU_MEDIA
{{< /highlight >}}

Now we clean what we downloaded, backup and reboot.  Hopefully everything works!

{{< highlight bash >}}
rm -r alpine-rpi-$VERSION-armhf.tar.gz new/
lbu ci
sync
reboot
{{< /highlight >}}
