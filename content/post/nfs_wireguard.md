---
title: NFS server over WireGuard in Alpine
date: 2021-05-21T13:27:31+02:00
categories: 
- alpine
- linux
---

I have recently built a new storage server at home consisting of 6x2TB hard
drives configured as RAID-Z2 with ZFS.  For the operating system I have chosen
Alpine Linux, which is a distribution that I really like for its
lightweightness and its simplicity.

Previously I had a storage server running Debian which I was sharing via sshfs.
sshfs is really easy to set up, as you just need to be running an ssh server,
nevertheless it has some disadvantages:
- On the client it runs via fuse, so all I/O operations go through userspace,
  adding overhead
- For each sshfs process, you can only access with a single user ID and group
  ID.  I use different users in my system so this is inconvenient.

I know that in Linux the de facto protocol to share a filesystem is NFS, but in
the past I decided not to use it because NFS doesn't run the protocol under an
encrypted channel, which is something that I wanted.  But now we have
WireGuard, which is a very performant and easy to set up VPN protocol, so I
decided to set up NFS sharing over WireGuard for my new storage server.

Here's my setup:
- server: Apline Linux (hostname: host.foo.bar)
- client: Arch Linux

Here are some reference I used to accomplish this setup:
- https://alexdelorenzo.dev/linux/2020/01/28/nfs-over-wireguard.html
- https://wiki.alpinelinux.org/wiki/Configure_a_Wireguard_interface_(wg)
- https://wiki.alpinelinux.org/wiki/Setting_up_a_nfs-server

# Wireguard

We will setup a wireguard connection between the server and the client using the following parameters:
- server
    - interface: wg0
    - IP: 10.8.0.1
- client
    - interface: wgNFS
    - IP: 10.8.0.2

## Server

First of all we install the wireguard tools required to generate keys and
manage the wireguard interface.
```sh
apk add wireguard-tools-wg wireguard-tools-wg-quick wireguard-tools-doc wireguard-tools
```

Then we load the wireguard module and configure our server to load it again on
boot.  In Alpine wireguard is already available in the kernel.
```sh
modprobe wireguard
echo "wireguard" >> /etc/modules
```

Now we need to generate a key pair.
```sh
umask 077 
wg genkey > privatekey
wg pubkey < privatekey > publickey
```

We edit the wireguard configuration for the interface `wg0` by editing the file
`/etc/wireguard/wg0.conf` with the following contents (where
`SERVER_PRIVATE_KEY` are the contents of the server's `privatekey` and
`CLIENT_PUBLIC_KEY` are the contents of the client's `publickey`, which is
generated in the next section):
```toml
[Interface]
ListenPort = 51820
PrivateKey = SERVER_PRIVATE_KEY

[Peer]
PublicKey = CLIENT_PUBLIC_KEY
AllowedIPs = 10.8.0.2/32
```

Don't forget to delete the privatekey file once you've copied it's contents in
the wireguard configuration file.
```sh
rm privatekey
```

Now we edit the network configuration file at `/etc/network/interfaces ` and
add the following, so that the wireguard interface is set up automatically
(Notice that we didn't set an interface address in the wireguard configuration,
but we are specifying it here):
```
auto wg0
iface wg0 inet static
        requires eth0
        use wireguard
        address 10.8.0.1
```

Now we start the wireguard interface manually (in the next reboot, it will be
started automatically):
```sh
ifup wg0
```

## Client

Install wireguard tools:
```sh
sudo pacman -S wireguard-tools
```

Like in the server, we create a pair of keys:
```sh
umask 077 
wg genkey > privatekey
wg pubkey < privatekey > publickey
```

I choose a different name for the client interface.  To configure wireguard we edit `/etc/wireguard/wgNFS.conf` (where
`CLIENT_PRIVATE_KEY` are the contents of the client's `privatekey` and
`SERVER_PRIVATE_KEY` are the contents of the servers's `publickey`, which is
generated in the previous section):
```toml
[Interface]
Address = 10.8.0.2/24
PrivateKey = CLIENT_PRIVATE_KEY

[Peer]
PublicKey = SERVER_PUBLIC_KEY
Endpoint = host.foo.bar:51820
AllowedIPs = 10.8.0.0/24
```

Don't forget to delete the privatekey file once you've copied it's contents in
the wireguard configuration file.
```sh
rm privatekey
```

Finally we manage the set up of the interface with systemd, and start it.
```sh
sudo systemctl enable wg-quick@wgNFS.service
sudo systemctl daemon-reload
sudo systemctl start wg-quick@wgNFS.service
```

The wireguard setup should be working now.  You can verify that you have a wireguard communication between server and client by doing pings over the wireguard interface.

From server:
```sh
ping 10.8.0.2
```

From client:
```sh
ping 10.8.0.1
```

Both ways should work if everything is working as expected.

# NFS

## Server

Install nfs utilities:
```sh
apk add nfs-utils nfs-utils-openrc nfs-utils-doc
```

We edit the nfs daemon configuration parameters in order to disable nfs version
2 and 3 (leaving only version 4, which is the latest), and we also instruct nfs
rpc to listen on the wireguard interface only.  To do this we edit the file
`/etc/conf.d/nfs` and change the corresponding part:
```sh
[...]

# Options to pass to rpc.nfsd
OPTS_RPC_NFSD="--no-nfs-version 2 --no-nfs-version 3 --nfs-version 4 --host 10.8.0.1 8"

# Options to pass to rpc.mountd
# ex. OPTS_RPC_MOUNTD="-p 32767"
OPTS_RPC_MOUNTD="--no-nfs-version 2 --no-nfs-version 3 --nfs-version 4"

[...]
```

We also create and edit the file `/etc/nfs.conf` to make the nfsd process to only listen on the wireguard interface:
```toml
[nfsd]
host=10.8.0.1
```

Finally, we add a line to `/etc/exports` to set the path we want to share over NFS:
```
/data          10.8.0.0/24(rw,sync,no_subtree_check,crossmnt,no_root_squash)
```

We run the following command to load the recently updated exports file:
```sh
exportfs -a
```

And finally we add the nfs service to the default target in OpenRC and start it.
```sh
rc-update add nfs
rc-service nfs start
```

## Client

On the client side, we add an entry to fstab indicating the NFS mount.  Using
systemd we specify the service requirements for this mount:
```sh
echo "10.8.0.1:/data   /data    nfs vers=4.2,_netdev,noauto,x-systemd.automount,x-systemd.requires=wg-quick@wgNFS.service" >> /etc/fstab
```

And finally, we restart the remote-fs systemd target which will trigger the NFS
mount by reading our fstab file.
```sh
sudo systemctl daemon-reload 
sudo systemctl restart remote-fs.target
```

Now in our client we should be able to access the storage folder at `/data`.
