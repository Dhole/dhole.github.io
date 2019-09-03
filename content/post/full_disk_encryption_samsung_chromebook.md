+++
Categories = ["arch linux", "linux"]
date = "2015-05-01T23:58:40+02:00"
title = "Full disk encryption on Samsung Chromebook with Arch Linux"

+++

In this post I will explain the procedure I followed to have an Arch Linux
install on a Samsung Chromebook 1 (XE303C12-A01US) with full disk encryption
using kernel 3.8.

# Kernel compilation and preparing SD card

## Install dependencies

Install the necessary depdendencies (In my case I was running ubuntu). Mainly
you need the tools for crosscompiling the kernel, configure u-boot and partition
the SD card with a GPT partition table.

{{< highlight bash >}}
sudo apt-get install u-boot-tools gcc-arm-linux-gnueabihf \
    binutils-arm-linux-gnueabihf cgpt device-tree-compiler
{{< /highlight >}}

## Set up some directories and download arch and kernel sources

{{< highlight bash >}}
TMP_PATH=$(pwd)/chromeos
mkdir -p $TMP_PATH
cd $TMP_PATH
mkdir -p root
mkdir -p mnt
{{< /highlight >}}

Download my custom files

{{< highlight bash >}}
git clone https://github.com/Dhole/alarm_install.git .
{{< /highlight >}}

Download Arch rootfs tarball

{{< highlight bash >}}
wget http://archlinuxarm.org/os/ArchLinuxARM-chromebook-latest.tar.gz
{{< /highlight >}}

Download kernel 3.8 with ChromeOS patches

{{< highlight bash >}}
KERNEL_BRANCH="chromeos-3.8"
git clone https://chromium.googlesource.com/chromiumos/third_party/kernel.git \
    -b $KERNEL_BRANCH --depth 1 chromeos
{{< /highlight >}}

## Build the kernel

Set up the config for the chromebook

{{< highlight bash >}}
cd $KERNEL_BRANCH
CROSS_COMPILE=arm-linux-gnueabihf- ARCH=arm make mrproper
./chromeos/scripts/prepareconfig chromeos-exynos5
{{< /highlight >}}

Configure the kernel as needed (Alternativelly, download my custom .config). In
my case I enabled most of the cipher options to be able to use AES-XTS in LUKS.
Be sure to disable "Treat compiler warnings as errors" in menuconfig

{{< highlight bash >}}
CROSS_COMPILE=arm-linux-gnueabihf- ARCH=arm make menuconfig
# or
cp ../files/.config .
{{< /highlight >}}

Compile the kernel

{{< highlight bash >}}
CROSS_COMPILE=arm-linux-gnueabihf- ARCH=arm make uImage -j2
CROSS_COMPILE=arm-linux-gnueabihf- ARCH=arm make modules -j2
CROSS_COMPILE=arm-linux-gnueabihf- ARCH=arm make dtbs -j2

rm -rf ../lib/modules/
CROSS_COMPILE=arm-linux-gnueabihf- ARCH=arm INSTALL_MOD_PATH=$TMP_PATH \
    make modules_install
{{< /highlight >}}    

Take the kernel.its from my files and make a u-boot image

{{< highlight bash >}}
# wget http://linux-exynos.org/dist/chromebook/snow/kernel.its \
#    -O arch/arm/boot/kernel.its
cp ../files/kernel.its arch/arm/boot/.
mkimage -f arch/arm/boot/kernel.its $TMP_PATH/vmlinux.uimg
cd $TMP_PATH
{{< /highlight >}}

## Prepare SD card

Set your SD card device

{{< highlight bash >}}
DISK=/dev/sde
sudo umount $DISK*
{{< /highlight >}}

Create a new disk label for GPT. Type y when prompted after running

{{< highlight bash >}}
sudo parted $DISK mklabel gpt
{{< /highlight >}}

Partition the SD card

{{< highlight bash >}}
sudo cgpt create -z $DISK 
sudo cgpt create $DISK 
sudo cgpt add -i 1 -t kernel -b 8192 -s 32768 -l U-Boot -S 1 -T 5 -P 10 $DISK 
sudo cgpt add -i 2 -t data -b 40960 -s 32768 -l Kernel $DISK
sudo cgpt add -i 12 -t data -b 73728 -s 32768 -l Script $DISK
{{< /highlight >}}

Create root partition

{{< highlight bash >}}
PART_SIZE=$(cgpt show $DISK | egrep '[0-9\ ]*Sec GPT table' | awk '{print $1}')
sudo cgpt add -i 3 -t data -b 106496 -s `expr $PART_SIZE - 106496` -l Root $DISK
{{< /highlight >}}

Tell the system to refresh what it knows about the disk partitions

{{< highlight bash >}}
partprobe $DISK
{{< /highlight >}}

Format partitions

{{< highlight bash >}}
sudo mkfs.ext2 "${DISK}2"
sudo mkfs.ext4 "${DISK}3"
sudo mkfs.vfat -F 16 "${DISK}12"
{{< /highlight >}}

## Install nv_uboot_fb

Download and install the nv_uboot bootloader with framebuffer support in the SD

{{< highlight bash >}}
wget -O - http://commondatastorage.googleapis.com/chromeos-localmirror/distfiles/nv_uboot-snow-simplefb.kpart.bz2 \
    | bunzip2 > nv_uboot.kpart
sudo dd if=nv_uboot.kpart of="${DISK}1"
{{< /highlight >}}

## Prepare the rootfs for encryption

Create key file. Store this file safely!

{{< highlight bash >}}
dd if=/dev/urandom of=rootfs.key bs=128 count=1
{{< /highlight >}}

Create luks container with key file

{{< highlight bash >}}
sudo cryptsetup luksFormat "${DISK}3" rootfs.key -c aes-xts-plain64 -s 256 --hash sha512
{{< /highlight >}}

Add password to luks container

{{< highlight bash >}}
sudo cryptsetup luksAddKey "${DISK}3" --key-file rootfs.key
sudo cryptsetup luksOpen "${DISK}3" alarm_rootfs -y --key-file rootfs.key
sudo mkfs.ext4 /dev/mapper/alarm_rootfs
sudo cryptsetup close alarm_rootfs
{{< /highlight >}}

## Install Arch Linux, kernel and custom files

### Mount LUKS and boot partition

{{< highlight bash >}}
sudo cryptsetup luksOpen "${DISK}3" alarm_rootfs -y --key-file rootfs.key
sudo mount /dev/mapper/alarm_rootfs root
sudo mount "${DISK}2" mnt
{{< /highlight >}}

Extract Arch Linux rootfs tarball

{{< highlight bash >}}
tar -xf ArchLinuxARM-chromebook-latest.tar.gz -C root
{{< /highlight >}}

Copy the kernel to the kernel partition

{{< highlight bash >}}
cp vmlinux.uimg mnt
rm -rf root/usr/lib/modules/3.8.11/
cp -R lib root/usr
{{< /highlight >}}

Copy custom mkinitcpio.conf (with crypt hook enabled)

{{< highlight bash >}}
cp files/mkinitcpio.conf root/etc
{{< /highlight >}}

Install initramfs from my files 

{{< highlight bash >}}
cp files/uInitrd.img mnt
{{< /highlight >}}

Alternatively, if you already have an Arch installation on your Chromebook you 
can create the initramfs yourself. From your Chromebook run as root.

{{< highlight bash >}}
pacman -S mkinitcpio uboot-mkimage
cp /root/files/mkinitcpio.conf /etc/mkinitcpio.conf
mkinitcpio -g ~/uInitrd.img
mount /dev/mmcblk1p2 /boot
mkimage -A arm -T ramdisk -C none -n initramfs -d ~/uInitrd.img /boot/uInitrd.uimg
umount /boot
{{< /highlight >}}


Install custom u-boot script to boot with kernel+initramfs

{{< highlight bash >}}
sudo mount "${DISK}12" mnt
mkdir -p mnt/u-boot
#wget http://archlinuxarm.org/os/exynos/boot.scr.uimg
mkimage -A arm -T script -C none -n 'Chromebook Boot Script' \
    -d boot_custom2.scr boot.scr.uimg
cp boot.scr.uimg mnt/u-boot
{{< /highlight >}}

*Optional*: Copy custom files for post-installation

{{< highlight bash >}}
cp files/arch_mkinitcpio.sh root/root/
cp files/postinstall.sh root/root/   
cp files/arch/private/mlan0-wrt54gl root/etc/netctl/
mkdir -p root/root/files/
cp -R files/arch/* root/root/files/
{{< /highlight >}}

### Umount LUKS and boot partition

{{< highlight bash >}}
sudo umount mnt
sudo umount root
sudo cryptsetup close alarm_rootfs
sync
{{< /highlight >}}

# Arch configuration

Boot your Chromebook and press Ctrl-U to boot from external drive. After you
see U-Boot start, press any kay to interrupt the boot process and type the
following in the prompt to reset the environment and save it to flash

{{< highlight bash >}}
env default -f
saveenv
reset
{{< /highlight >}}

You can now boot the Chromebook into Arch and configure the system. Login as 
root to continue.

Configure and connect wifi

{{< highlight bash >}}
wifi-menu mlan0
{{< /highlight >}}

Configure locale, timezone and hostname

{{< highlight bash >}}
MYHOSTNAME="alarm"
USERNAME="dhole"

locale-gen
localectl set-locale LANG=en_US.UTF-8
timedatectl set-timezone Europe/Madrid
hostnamectl set-hostname $MYHOSTNAME
{{< /highlight >}}

Add user

{{< highlight bash >}}
pacman -Sy
pacman -S sudo
useradd -m -G users -s /bin/bash $USERNAME
passwd $USERNAME
visudo # uncomment the wheel group
usermod -a -G wheel $USERNAME
{{< /highlight >}}

# Post install

At this point you should have a bootable full disk encryption Arch Install.
In the following lines I will detail the post installation steps I follow to
cover my needs in the laptop. Run all the following commands as root.

Install some packages (tune this to your needs)

{{< highlight bash >}}
pacman -S mesa-libgl xorg-server xorg-xinit xorg-server-utils mesa xf86-video-fbdev \
xf86-input-synaptics unzip dbus lightdm lightdm-gtk-greeter gnome-icon-theme xfce4 \
firefox midori gnome-keyring wget vim ttf-dejavu ttf-ubuntu-font-family htop strace \
lsof i3 xscreensaver git conky dmenu profont dina-font tamsyn-font alsa-utils ntp \
pm-utils p7zip xarchiver unrar zip python-pip tmux mpv mc make tmux iputils rtorrent \
youtube-dl macchanger tree acpid pulseaudio pulseaudio-alsa mupdf clang file gvim \
mosh nmap rxvt-unicode thunar adduser rsyslog wicd chromium xf86-video-armsoc-chromium \
i3lock
{{< /highlight >}}

Disable clearing of boot messages

{{< highlight bash >}}
mkdir -p /etc/systemd/system/getty@tty1.service.d/
echo -e "[Service]\nTTYVTDisallocate=no" > /etc/systemd/system/getty@tty1.service.d/noclear.conf
mkdir -p /etc/ld.conf/
echo "/usr/local/lib" >> /etc/ld.conf.d/local.conf
{{< /highlight >}}

Install fonts http://linuxfonts.narod.ru/

{{< highlight bash >}}
cp /root/files/fonts.conf /etc/fonts/conf.d/99-my-fonts.conf
cd /usr/share
7z e /root/files/fonts.7z
cd /root
{{< /highlight >}}

Enable suspend and xscreen lock on lid close: 
https://blog.omgmog.net/post/making-suspend-on-lid-close-work-with-arch-linux-on-the-hp-chromebook-11/

{{< highlight bash >}}
cp /root/files/handler.sh /etc/acpi/handler.sh
systemctl enable acpid
{{< /highlight >}}

Install custom touchpad, keyboard, evdev

{{< highlight bash >}}
cp /root/files/xorg.conf.d/* /etc/X11/xorg.conf.d
{{< /highlight >}}

Enable lightdm

{{< highlight bash >}}
systemctl enable lightdm
{{< /highlight >}}

Set default brightness on power up and script to change it

{{< highlight bash >}}
cp /root/files/brightness.conf /etc/tmpfiles.d/brightness.conf
cp /root/files/chbr /usr/local/bin/chbr
{{< /highlight >}}

Configure pulseaudio

{{< highlight bash >}}
echo "load-module module-alsa-sink device=sysdefault" >> /etc/pulse/default.pa
{{< /highlight >}}

Enable rsyslog

{{< highlight bash >}}
systemctl enable rsyslog.service
systemctl start rsyslog.service
{{< /highlight >}}

Change MAC at every connection

{{< highlight bash >}}
cp /root/files/mac_change /etc/wicd/scripts/preconnect/
{{< /highlight >}}

Fix wicd-curses: 
https://github.com/voidlinux/void-packages/commit/220de599ad3ecba14423289209a3e4e031037edf

{{< highlight bash >}}
cp /root/files/netentry_curses.py /usr/share/wicd/curses/
{{< /highlight >}}

Enable eduroam for wicd: 
http://chakraos.org/wiki/index.php?title=Wicd#Making_eduroam_work_with_wicd 
This setup is working for eduroam at Universitat Politècnica de Catalunya

{{< highlight bash >}}
cp /root/files/ttls-80211 /etc/wicd/encryption/templates/
cd /etc/wicd/encryption/templates
echo ttls-80211 >> active
cd /root
mkdir -p /etc/ca-certificates/custom/
cp /root/files/AddTrustExternalCARoot.crt /etc/ca-certificates/custom/
{{< /highlight >}}

Chromium defaults

{{< highlight bash >}}
cp /root/files/chromium_default /etc/chromium/default
{{< /highlight >}}

Install wicd saved networks (This is only for my personal usage, this config
is not in github)

{{< highlight bash >}}
cp /root/files/private/wireless-settings.conf /etc/wicd/
systemctl enable wicd
{{< /highlight >}}

Install my custom configuration for the user from my dot_files github repo. This
contains my vim settings, i3 window manager configuration for chromebook, 
bashrc, tmux.conf, etc. Login as your user to run the following commands.

{{< highlight bash >}}
cd ~
mkdir -p github
cd github
git clone https://github.com/Dhole/dot_files.git
cd dot_files
cp -R .* ~
cp ALARM/.* ~
sh vim_setup.sh
{{< /highlight >}}

# TODO

There are only two things which I find missing from my installation.

One is fixing an annoying issue with suspend: my chromebook wakes from sleep 
after 10 minutes or so when the lid is closed. I've tryed using both suspend from
systemctl and from pm-suspend. I think this may be related to the kernel 3.8, 
since I didn't have this issue on 3.4 (well, not really, my laptop would wake
up some times, but it was not usual).

The other one is doing the installation on the internal eMMC. Unfortunately the
SD card slot in the chromebook is placed very close to the end of the board, so
half of the SD card sticks out; it doesn't look nice and I fear for the SD card
getting stuck somewhere when moving my chromebook around.

# Resources

The installation process of Arch Linux on the Samsung Chromebook is taken from 
[1], [2] and [3]. The procedure to compile and install of kernel 3.8 is taken from
[0]. The instructions to boot with initramfs to enable full disk encryotion 
are taken from [4], and a reference for doing an install with full disk encryption
can be found at [5].

[0] https://elatov.github.io/2014/11/install-chromeos-kernel-38-on-samsung-chromebook/

[1] https://elatov.github.io/2014/02/install-arch-linux-samsung-chromebook/

[2] http://archlinuxarm.org/platforms/armv7/samsung/samsung-chromebook

[3] http://linux-exynos.org/wiki/Samsung_Chromebook_XE303C12/Installing_Linux

[4] http://archlinuxarm.org/forum/viewtopic.php?f=47&t=7071

[5] https://dvikan.no/the-smallest-archlinux-install-guide
