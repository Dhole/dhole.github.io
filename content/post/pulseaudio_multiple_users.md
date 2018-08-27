---
Categories = ["pulseaudio"]
title: "Pulseaudio for multi-user Linux"
date: 2018-08-27T20:54:53+02:00
---

# My setup

For some time I've been using several unix users for my daily work in my
desktop computer.  After trying out Qubes OS for some time (an OS that achieves
security by compartmentalization: different kinds of activites are performed in
a different VM, isolating the data of each activity from each other), I came
back to GNU/Linux and realized that there's already a security separation in
Unix (albeit not as secure as virtualization as in Qubes): users.

So lately I'm using a user for browsing, another for playing audio and video,
another for developing, etc.  This way, if an attacker succesfully exploits my
web browser, they won't be able to access my ssh nor gpg keys (unless they are
able to escalate privileges).

# PulseAudio

Here comes PulseAudio, which has a default configuration to run as a single
user.  After playing around with the configuration I found this to work for my
needs:

- pulseaudio server runs as my main user (I could actually create a new user
  just to run the pulseaudio server)
- Every user that belongs to the `audio` group is able to access the pulseaudio
  server (and thus play sound).

For this, I just need to add the required users to the `audio` group:

```
usermod -aG audio user
```

The following setup creates the pulseaudio server unix socket at a place where
every user can find it, and only accepts users that belong to the `audio`
group.  Data transfer of audio will happen via memfd shared memory.

`/etc/pulse/client.conf`:
```
autospawn = no
default-server = unix:/tmp/pulse-server
enable-memfd = yes
```

`/etc/pulse/daemon.conf` was not modified from the default.

`/etc/pulse/default.pa` (Only showing the relevant part):
```
[...]

### Load several protocols
load-module module-dbus-protocol
.ifexists module-esound-protocol-unix.so
load-module module-esound-protocol-unix
.endif
load-module module-native-protocol-unix auth-group=audio socket=/tmp/pulse-server

[...]
```

The only remaining part is starting the pulseaudio server as my main user:
```
pulseaudio -D
```
