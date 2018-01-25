+++
Categories = ["PocketCHIP", "kernel"]
date = "2017-11-23T14:35:56-08:00"
title = "Enabling LUKS on the PocketCHIP"
+++

# Introduction

I've recently acquired a handheld ARM computer with screen and keyboard called
the [PocketCHIP](https://getchip.com/pages/pocketchip).  The main board on the
device is called the [CHIP](https://getchip.com/pages/chip), which is a tiny
ARM computer capable of running Linux that is sold for $9.

After flashing it with the *CHIP 4.4 GUI* OS, a flavor of Debian released by
Next Thing Co (the company that made the PocketCHIP)  I noticed I wasn't able
to mount LUKS-encrypted partitions due to missing kernel modules.  In this post
I will explain what I had to do to build and install the missing modules
without the need to replace the entire kernel.  If you want to install a new
and different kernel you will need to follow a more involved process because
the WiFi and GPU drivers aren't in the kernel sources and require you to build
them apart (and also fiddle with the device tree).

# Required toolchain

In order to build the Linux kernel from an x86_64 machine for ARM, we need a
cross-compiling toolchain, which includes a cross-compiling GCC among other
tools.  I have recently installed [Gentoo](https://www.gentoo.org/) on a
laptop, which has an awesome tool to build cross-compiling environments for
many combinations of architectures and settings.  If you are using another
distribution like a Debian-based one you probably need to install
`gcc-arm-linux-gnueabihf`

On Gentoo as root, run the following to install a cross-compiling environment
for armv7a, the CPU architecture of the CHIP (this will take a while):
```bash
crossdev -S -v -t armv7a-hardfloat-linux-gnueabi
```

# Building

As a regular user, set up the environment variables needed to enable
cross-compiling the kernel, and create some working folders:

```bash
export ARCH=arm
export CROSS_COMPILE=armv7a-hardfloat-linux-gnueabi-
export WORKSPACE=~/proj/CHIP/4.4.13-ntc-mlc/
mkdir -p $WORKSPACE
mkdir -p ~/git/CHIP
```

Now let's clone the kernel source git repository from Next Thing Co.  We will
be getting the branch that was used to build the kernel shipped in the *CHIP
4.4 GUI* release:
```bash
cd ~/git/CHIP
git clone --single-branch -b debian/4.4.13-ntc-mlc https://github.com/NextThingCo/CHIP-linux.git
cd CHIP-linux
```

Before configuring the kernel, we will copy the configuration that was used to
build the kernel in *CHIP 4.4 GUI*.  We can get the file from the PocketCHIP at
`/boot/config-4.4.13-ntc`.  I recommend having `sshd` enabled on the PocketCHIP
to transfer files over WiFi with ease.
```bash
cp config-4.4.13-ntc .config
```

We create the empty file `.scmversion` in order to disable the "+" at the end
of the kernel version that gets embedded into the modules in the *vermagic*
property.  If we don't generate modules with the same *vermagic* as the one in
the installed kernel, the modules will fail to load.
```bash
touch .scmversion
```

Now we can proceed to configure the kernel to enable the modules we need.  In
my case, I enabled the modules needed for LUKS:
```bash
make menuconfig
```

## make menuconfig options

Taken from the [Dm-crypt Gentoo wiki
entry](https://wiki.gentoo.org/wiki/Dm-crypt), here are the options needed to
enable LUKS.

Enable the crypt target for the device mapper:
```
Device Drivers --->
    [*] Multiple devices driver support (RAID and LVM) --->
        <M> Device mapper support
        <M>   Crypt target suppor
```

Enable the cryptographic API modules required for LUKS:
```
[*] Cryptographic API --->
    <M> XTS support
    <M> SHA224 and SHA256 digest algorithm
    -*- AES cipher algorithms
    <M> User-space interface for hash algorithms
    <M> User-space interface for symmetric key cipher algorithms
```

Optionally, enable the following modules of the cryptographic API to support
TrueCrypt/VeraCrypt compatibility mode:
```
[*] Cryptographic API ---> 
     <M> RIPEMD-160 digest algorithm 
     <M> SHA384 and SHA512 digest algorithms 
     <M> Whirlpool digest algorithms 
     <M> LRW support 
     <M> Serpent cipher algorithm 
     <M> Twofish cipher algorithm
```

Finally, and very importantly, set the local version of the kernel to
`-ntc-mlc` in order to get the same *vermagic* as the installed kernel:
```
 General setup  --->
  () Local version - append to kernel release
```

## Build and install

We can now make the kernel and modules for ARM (in this case I'm setting `-j4`
to use 4 parallel building threads).  This will take a while:
```bash
make -j4
```

We install the modules in our workspace:
```bash
make INSTALL_MOD_PATH=$WORKSPACE modules_install
```

Now, on the CHIP as root, we make a folder to store the new modules we want to install:
```bash
mkdir -p ~/modules/{crypto,drivers/md/}
```

We copy the built modules to the CHIP:
```bash
scp crypto/*.ko root@192.168.0.106:~/modules/crypto/
scp drivers/md/dm-crypt.ko root@192.168.0.106:~/modules/drivers/md/
```

Finally, on the CHIP as root, we copy the modules we just transfered to their
destination so that the kernel can load them:
```bash
cp -n ~/modules/crypto/*.ko /lib/modules/4.4.13-ntc-mlc/kernel/crypto/
cp ~/modules/drivers/md/dm-crypt.ko  /lib/modules/4.4.13-ntc-mlc/kernel/drivers/md/
```

There's no reboot needed.  You should be able to mount LUKS partitions using
`cryptsetup` without problems at this point.  You can easily test that everything is working by running a benchmark:
```bash
cryptsetup benchmark
```
