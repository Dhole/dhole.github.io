+++
Categories = ["debian", "reproducible builds", "linux"]
date = "2015-05-10T17:14:05+02:00"
title = "Reproducible builds on Debian for GSoC 2015"

+++

This is the first blog post of a series I will be writing about my experiences contributing to Debian for Google Summer of Code 2015.

# A bit about myself
I'm a Spanish student doing a master's in Computer Science in Barcelona. I graduated on Electrical Engineering (we call it Telecommunications here). I've always been interested in computing and programming and I have worked on several projects on my own using C, python and go. My main interests in the field are programming languages, security, cryptography, distributed and decentralized systems and embedded systems.

I'm an advocate of free software, I try to use it as much as I'm able to in my devices and also try to convince my friends and family of its benefits. I have been using GNU/Linux for nearly ten years as my main operating system and I have tried several *BSD's recently.

One of my latest personal projects is a [gameboy emulator](https://github.com/Dhole/miniBoy) written in C (still work in progress) which already plays many games (without sound though) . You can find other minor projects in my [github page](https://github.com/Dhole) (I try to publish all the code I write online, under free software licence)

After so many years of using free software and benefiting from it, I thought it was about time to contribute back! That's why I gave GSoC a try and applied to work on the Reproducible Builds project for Debian :) And I got accepted!

# Reproducible Builds
The idea behind this project is that currently many packages aren't built in a reproducible manner; that is, they contain timestamps, building machine name, unique IDs, and results from other processes that happen differently between machines, like file ordering in compressed files. The project aims to patch all the Debian packages / the building scripts in order to generate the same binary (bit by bit) independently of the machine, timezone, etc where it is built. This way, a cryptographic hash of the built package can be distributed and many people can rebuild the package to verify that the binary in the repositories indeed corresponds to the right source code by means of comparing the hash.

## Motivation
One of the main advantages of the free software is that source code is available for peer review. This makes it easier for users to trust their software, as they can check the source to verify that the program is not doing anything bad. Even if the user doesn't do that, they can trust the wider community with that task. But many distributions serve packages in binary form, so how do we know that the binary comes from the publicly available source code? The current solution is that the developers who build the packages sign them cryptographically; but this lands all the trust to the developer and the machines used for building.

I became interested in this topic with a [very nice talk](https://www.youtube.com/watch?v=5pAen7beYNc) given at 31c3 by Mike Perry from Tor and Seth Schoen from the EFF. They focused on reproducible builds applied to the tor browser bundle, showing a small demo of how a building machine could be compromised to add hidden functionalities when compiling code (so that the developer could be signing a compromised package without their knowledge).

## Benefits
There are two main groups who benefit with reproducible builds:

### For users
The user can be more secure when installing packages in binary form since they don't need to trust a specific developer or building machine. Even if they don't rebuild the package by themselves to verify it, there would be others doing so, who will easily alert the community when the binary doesn't match the source code.

### For developers
The developer no longer has the responsibility of using his identity to sign the package for wide distribution, nor is that much responsible of the damage to users if their machine is compromised to alter the building process, since the community will easily detect it and alert them. 

This later point is specially useful with secure and privacy aware software. The reason is that there are many powerful organizations around the world with interest on having backdoors in widely used software, be it to spy on users or to target specific groups of people. Considering the amount of money these organizations have for such purposes, it's not hard to imagine that they could try to blackmail developers into adding such backdoors on the built packages. Or they could try to compromise the building machine. With reproducible builds the developer is safer, as such attack is no longer useful.

# Reproducible Builds in Debian
The [project](https://wiki.debian.org/ReproducibleBuilds) kicked-off at Debian at mid 2013 , leaded by Lunar and soon followed by many other developers (h01ger, deki, mapreri, ...). Right now about 80% of the packages in the unstable branch of Debian can be built reproducibly. The project is very active, with many developers sending [patches](https://bugs.debian.org/cgi-bin/pkgreport.cgi?usertag=reproducible-builds@lists.alioth.debian.org) every week. 

A machine running [Jenkins](https://reproducible.debian.net/reproducible.html) (which was set up at the end of 2012 for other purposes) is being used since late 2014 to continuously build packages in different settings to check if they are built reproducibly or not.

In order to analyze why packages fail to build reproducibly, a tool called **debbindiff** has been developed, which is able to output in text or html form a smart diff of two builds. 

Another tool called **strip-nondeterminism** has been developed to remove non-determinism from files during the building process.

For this GSoC I plan on helping improving these tools (mainly debbindiff), write many patches to achieve reproducibility in more packages and write documentation about it. Some of the packages fail to build reproducibly due to specifics of their building processes, whereas others fail due to the usage of toolchains that add non-determinism. I'll focus more on the later ones in order to improve the state more packages. akira will also be working on this project for this GSoC.

Finally, I just want to add that I'm looking forward to contribute to Debian, meet the community and learn more about the internals of this awesome distribution!
