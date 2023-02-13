+++
title = "Collapse Ready Operating Systems - Intro"
date = 2023-02-13T12:23:20+02:00
Categories = ["linux", "bsd"]
+++

# Introduction

Nowadays we live in a hyperconnected World that relies heavily on Internet
connection for day to day tasks in all levels.  I'm not very happy with this
relience of assuming Internet access 24h for everything, as I think it
disempowers the user.

For example, whereas people before used to buy and own media, now they buy a
license to stream such media from the cloud.  This means that the user only has
access to the media as long as the platform exists, and we know that this is no
guarantee for the future.  It also means that the user can't easily share the
media with their friends, that the consumption of the media can only be done in
authorized devices, etc.

I believe this reliance on 24h access makes us more lazy as we don't need to
prepare things ahead of time: for example when traveling, there's no much need
to prepare the trip because you can just search for things to do once you
arrive from your smartphone.

These are just two quick negative points that I think about, but I'm sure there
are more.  In general, I believe this situation makes us extremely dependant on
Internet access, and makes us very uncapable of basic tasks when there's no
Internet.  Following this train of thought makes me wonder what would happen if
there was a collapse where Internet stopped being available for an undetermined
period of time?  How could I prepare myself for that?

# A Collapse Ready Operating System

The fictional situation is the following: there has been some sort of social
collapse and the Internet infrastructure is gone: there's no more Internet for
us.  Now imagine that in this situation we still find value in our computers;
how would we operate them now that we don't have Internet?

I would like to analyze which Operating Systems would be suitable to for this
imaginary scenario.  In particular I would like to evaluate the Operating
System at the following points:
- Can I store a software repository with the programs that I or someone in my
  area may need?
- Can I store the source code corresponding to the software repository so that
  I or someone else can fix potential bugs or extends the programs that we
  may need to use?
- Can I create new installation images from the OS itself, so that I can
  install it in other computers?
- Can I store the OS source code so that I or someone else can fix potential
  bugs or extend the OS funcionality / support and from it build installation
  images of the OS?
And can I achieve all this offline?

I will try to answer these questions for different Operating Systems in order
to evaluate their collapse-readiness (according to the scenario explained).

For my setup I will use:
- Thinkpad T480s with 8 GiB of RAM and 512 GiB of SSD storage
    - This will be the main laptop used to test the OS.
- External 2.5" hard drive of 2 TiB
    - This external drive will be used to store the source code / binaries of
      the software repository
- Thinkpad x220 with 8 GiB of RAM and 256 GiB of SSD storage
    - This will be the device onto which I will try to install the OS
      bootstrapped from the laptop device.

There are more aspects a part from the ones related to the questions I asked
that could be interesting to analyze a collapse-ready OS.  For example: driver
support, power management, reliability, speed, etc.  Nevertheless this is a
fictional exercise so I will focus on the 4 questions and their context for
these post series.

See you soon in the next post!
