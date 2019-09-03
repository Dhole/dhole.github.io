+++
Categories = ["alpine", "raspberry pi", "linux"]
date = "2016-10-20T15:03:12-07:00"
title = "Raspberry Pi 2 I/O benchmarks"

+++

# Introduction

I'm currently setting up a Raspberry Pi 2 as a home server for various services.
I'm gonna write a series of blog posts about how I configured my Raspberry Pi to
achieve my goals, which will be mainly setting up a git server and a backup
server.

# Choice of distribution

I discovered [Alpine Linux](https://alpinelinux.org/) while searching
lightweight distributions for the Raspberry Pi.  This is a lovely small Linux
distribution: one of the first things I noticed is how fast it runs on the RPi
due to using a ram filesystem by default; this is specially noticeable in the
RPi because usualy the operating system resides in the micro-SD card, which
usually offers really slow read and write operations.  Another really nice
feature is that it's security-oriented, and as such the kernel is patched with
[grsecurity/PaX](https://www.grsecurity.net/) and the userland binaries (I
understand that means all packages- too) are compiled with hardening features:
[Position Independent Executables
(PIE)](https://en.wikipedia.org/wiki/Position-independent_code) and [stack
smashing protection](http://wiki.osdev.org/Stack_Smashing_Protector).  This
distribution uses [musl libc](https://www.musl-libc.org/) instead of glib and
[busybox](https://busybox.net/) to provide all the basic utilities, decisions
that help making it small and lightweight.  I should also mention that OpenRC is
used for the init system (instead of following the current trend of switching to
systemd).

# Personal requirements

Now that I have choosen a distribution, I have a requierement for my setup: all
the personal data I store in the RPi (git repositories, backups, websites) must
be encrypted in the disk.

# Benchmarks

I'm mainly interested in how fast files can be written on the encrypted
partition.  This files will probably be comming from the network.

## Setup

To achieve better I/O and to avoid damaging the micro-SD (or a USB stick) I'm
gonna use an external USB hard disk (western digital My Passport) for storage.

The RPi will be connected to a 1 Gbps switch (which shouldn't matter considering
that the Ethernet interface of all the RPis are 10/100 Mbps).

## cryptsetup

This test will give us the encryption/decryption speeds running from memory, so
they represent an upper bound on the write speed that we can achieve in disk.

```
lizard:~/git/public/test.git$ cryptsetup benchmark
# Tests are approximate using memory only (no storage IO).
PBKDF2-sha1        42555 iterations per second for 256-bit key
PBKDF2-sha256      73635 iterations per second for 256-bit key
PBKDF2-sha512      33781 iterations per second for 256-bit key
PBKDF2-ripemd160   36408 iterations per second for 256-bit key
PBKDF2-whirlpool   11497 iterations per second for 256-bit key
#  Algorithm | Key |  Encryption |  Decryption
     aes-cbc   128b    12.6 MiB/s    14.8 MiB/s
 serpent-cbc   128b           N/A           N/A
 twofish-cbc   128b           N/A           N/A
     aes-cbc   256b    10.9 MiB/s    11.2 MiB/s
 serpent-cbc   256b           N/A           N/A
 twofish-cbc   256b           N/A           N/A
     aes-xts   256b    14.6 MiB/s    14.4 MiB/s
 serpent-xts   256b           N/A           N/A
 twofish-xts   256b           N/A           N/A
     aes-xts   512b    11.2 MiB/s    11.0 MiB/s
 serpent-xts   512b           N/A           N/A
 twofish-xts   512b           N/A           N/A
```

My encrypted partition is using AES-XTS (this mode is the current
recommendation) with 256 bit keys, so we achieve **14.6 MiB/s** and **14.4
MiB/s** for encryption (write) and decryption (read).

## FAT32 write speed (dd)

For a baseline comparison, I test the write speed of an unencrypted FAT32 file
system.

```
lizard:/mnt/slowpoke# time dd bs=1M count=4096 if=/dev/zero of=test conv=fsync
4096+0 records in
4095+1 records out
real    11m 28.47s
user    0m 0.08s
sys     0m 45.25s
```

The measurement of write speed is **5.95 MB/s**.  That's much lower than what I
was expecting.  I achieve write speeds of 40 MB/s from my laptop on the same
external disk.

## LUKS + ext4 write speed (dd)

This test should theoretically give upper bound results for my setup.

```
lizard:/mnt/wd_ext# time dd bs=1M count=4096 if=/dev/zero of=test conv=fsync
4096+0 records in
4096+0 records out
real    21m 23.27s
user    0m 0.07s
sys     0m 36.35s
```

That's just **3.19 MB/s**, which is extremely slow.

## LUKS + ext4 (rsync)

This test measures exactly one of my use cases, as I plan to use rsync for my
backups.

```
 % rsync -v --progress movie.mp4 green-local:/mnt/disk/
movie.mp4
  1,991,346,871 100%    9.17MB/s    0:03:27 (xfr#1, to-chk=0/1)

sent 1,991,833,155 bytes  received 35 bytes  9,553,156.79 bytes/sec
total size is 1,991,346,871  speedup is 1.00
```

Surprisingly this one gives much better results than the `dd` tests: **9.11
MB/s**.

# Conclusions

First of all, I don't understand why the `dd` tests performed so badly.  The
`fsync` option should make sure that data is written to disk and not cached:

```
        conv=fsync      Physically write data out before finishing
```
Maybe there's a bug in busybox's dd?  Or am I missing something?  I was
expecting to find the same speeds as LUKS encryption speeds here.

The rsync test gives us the best performance we could expect, considering that
the limit comes from the 100 Mbit Ethernet, we won't be able to transfer data at
higher speeds than ~10 MB/s.  In this case, the usage of disk encryption isn't
making things slower.

So overall I'm expecting to get transfer speeds (including writing to the
encrypted partition) of about **9-10 MB/s**.  I'm happy with this and I believe
it should suit my needs, as I plan do backups every day in my local network.

In the next post I will explain how to set up a git server with a web interface.
Stay tunned!
