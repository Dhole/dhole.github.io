+++
Categories = ["fedora", "linux"]
title = "Thinkpad Helix 2 with Linux"
date = "2019-09-03T20:54:53+02:00"
+++

# Preface

Recently I've bought a second hand Thinkpad Helix 2nd Gen with the intention of
using it mainly as a tablet to read PDF documents and comics (although I may
use it for Internet browsing and occasional development).  I like running free
software on my computers and so I decided to use GNU/Linux with this
tablet/laptop.  Here I will explain all the issues I encountered and how I
solved them.

# First approach

Initally I installed Arch Linux as it's the distro I've been most comfortable
with during the past years.  I decided to go with GNOME desktop for its
touchscreen integration.  Some things worked, some others didn't.  I managed to
get everything working except for the sound on the tablet speakers mainly
following the [Arch wiki article about the
laptop](https://wiki.archlinux.org/index.php/Lenovo_ThinkPad_Helix_2nd_Gen),
which was extremely helpful.  Appart from the sound there was the automatic
screen rotation which I got to work but after some reboots stopped working and
I didn't figure out why.

# Second approach

While annoyed with the tablet speakers not working, I decided to try another
distro: Fedora.  I was happy to discover that on the Fedora 30 live the
speakers were working!  I also told myself that maybe Arch Linux was not the
best candidate for a device that I want to use mainly for media, for which I
want the minimum amount of maintainence, so I decided to install Fedora.

# Fedora

After installing Fedora most of the stuff worked, and I followed the same
procedures I followed with Arch to get the rest of the system working the way I
wanted.  Some of the fixes required more work.  Here's all that I did.

## Disabled sysrq

It seems that sysrq is disabled nowadays.  I like being able to do an emergency
sync of the filesystem when the system hangs, so I added the following line to
the `GRUB_CMDLINE_LINUX` in `/etc/default/grub`: `sysrq_always_enabled=1`.

## Suspend not working properly

As explained in the Arch wiki, it seems that the pro keyboard keeps sending
ACPI interrupts to the tablet that makes it wake up immediately after
suspension.  To ignore these ACPI wakeup interrupt I added the following line
to the `GRUB_CMDLINE_LINUX` in `/etc/default/grub`: `acpi.ec_no_wakeup=1`.

## rngd process consuming a lot of CPU

After installation there was a daemon called `rngd` that was using several CPU
cores making everything go slow.  It seems that this is a daemon that collects
entropy and feeds the kernel and is specially useful during the boot proces,
where randomness may be required but there's no much entropy because not many
events have happened yet.  Since the system is already installed I guess it's
safe to disable this service and rely on the normal kernel entropy gathering
process: `sudo systemct stop rngd`, `sudo systemctl disable rngd`.

## kworker consuming CPU

I observed in top that thre was a kworker process taking half of a core all the
time while the system was idle.  This affected the battery consumtion (as
reported by `powertop`).  After some searches in duckduckgo I found out that a
possible culprit could be an ACPI event sending too many interrupts.  After an
analysis I discovered it was the ACPI interrupt `gpe0B`.  I wanted to figure
out if it was safe to disable the handling of this interrupt and found [this
excellent post in reddit explaining how to figure out what hardware module is
related to that ACPI
interrupt](https://old.reddit.com/r/linux/comments/3lfxhf/a_linux_powersaving_tip_for_noobs_like_me/cv64849/).
I followed the process described in the post and discovered that the interrupt
was related to an NFC module.  I think think my laptop has NFC, so I proceeded
to disable the interrupt: `echo mask > /sys/firmware/acpi/interrupts/gpe0B`.
And to make it permanently, I added the following line to the
`GRUB_CMDLINE_LINUX` in `/etc/default/grub`: `acpi_mask_gpe=0x0b`.

For the curious, here's the disassembly of the dsdt (the DLS that handles each
ACPI interrupt) that takes care of the gpe0B event:
```
        Method (_L0B, 0, NotSerialized)  // _Lxx: Level-Triggered GPE, xx=0x00-0xFF
        {
            If ((GPFG && \_SB.PCI0.LPC.NFCI))
            {
                GPFG = 0x00
                Notify (\_SB.PCI0.SMBU.NFC, 0xC0) // Hardware-Specific
            }
        }
```

## LCD flicker

The brightness control of the display works via PWM.  On full brightness, the
light is continuous.  When you start diminishing the brigtness, the light
toggles very fast staying a percentage of time on.  By default I find the PWM
frequency too low, so I can notice the light flickering causing discomfort.
Luckily the frequency of the PWM can be increased!  To do this I installed the
tool `intel-gpu-tools` which allows reading and writing to the gpu control
registers.  The following command will set the PWM frequency to 500 Hz, which
works for me: `sudo intel_reg write 0xC8254 0x1770177`.

## Tablet speakers not working (wait, again?)

Yes, after upgrading the kernel the tablet speakers stopped working.  Now I
know why they didn't work in Arch Linux.  It's time to boot with the older
kernel (choose it in the grub menu).

## Touchpad not working after keyboard re-attach

I already encountered this issue and had a solution for Arch: I would unload
and load the mouse module and the touchpad would work again.  But things were
not as easy in Fedora because the module is built-in the kernel!  So it's time
to build the kernel by myself :D  Mainly I followed this [excellent guide
provided by the Fedora
wiki](https://fedoraproject.org/wiki/Building_a_custom_kernel).  Since I needed
an older kernel I had to checkout an old commit of the `f30` branch.  `fedpkg
local` gave me some isses related to the checkout not being the HEAD of the
branch, so I just created a new branch from that checkout.  Also don't forget
to run `sudo dnf builddep kernel.spec` after downloading the kernel package
sources to install the build dependencies.  Now, the important part is to
change the config so that the mouse module is built as a module and not
built-in.  To do so, add this line to `kernel-local`:
```
CONFIG_MOUSE_PS2=m
```
This will create the `psmouse` module.
Now, reloading the module manually everytime you re-attach the keyboard is a
bit annoying right?  Let's use the `acpid` daemon to do it automatically for
us!  Firs install the daemon and enable it: `sudo dnf install acpid`, `sudo
systemctl start acpid`, `sudo systemctl enable acpid`.  Now let's add a handler
for the attach ACPI event that will reload the mouse module.

`/etc/acpi/events/ibmhotkey`:
```
event=ibm/hotkey.*
action=/etc/acpi/actions/ibmhotkey.sh %e
```

`/etc/acpi/actions/ibmhotkey.sh`
```
#!/usr/bin/sh

set -e

PATH=/usr/sbin:/usr/bin

case "$1" in
	ibm/hotkey)
		case "$4" in
			00004013)
				logger "Tablet detached"
				;;
			00004012)
				logger "Tablet docked"
				modprobe -r psmouse
				modprobe psmouse proto=auto
				;;
		esac
		;;
esac
```
And don't forget to give execution rights to the handler: `sudo chmod +x
/etc/acpi/actions/ibmhotkey.sh`.

# FIN

And that's it!  Everything is working now and I feel happy with the results.  I
may automate the display light PWM frequency so that it gets set at boot and
maybe after every wakeup (as it seems it gets back to the default low frequency
PWM).

# Acknowledgements

I would like to thank the people that maintain the fantastic Arch Linux wiki,
which is a resource I usually use no matter which distro I'm using (and also to
Arch developers for maintaining this great distro).  Thanks to all the
developers that make Fedora possible!  And thanks for the reddit user Nanosleep
for the insight on debugging how the ACPI events are handled.
