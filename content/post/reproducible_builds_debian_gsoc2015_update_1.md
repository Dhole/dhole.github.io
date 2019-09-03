+++
Categories = ["debian", "reproducible builds", "linux"]
date = "2015-08-06T20:12:15+02:00"
title = "Reproducible builds on Debian for GSoC 2015, 1st update"

+++

This is the second blog post I'm writing about my experiences contributing to Debian for Google Summer of Code 2015 (check my [first post](/post/reproducible_builds_debian_gsoc2015/))

# Status update

## First month

It's been two months and a few days since the GSoC started. During the first month I worked on fixing specific packages, mainly concerning issues with timestamps, which is a very common source of unreproducibility. In many cases, during the build process files are compressed into gzip or zip archives, which store the creation time of files in the metadata. This can lead to unreproducible results when there is timezone variation between builds (easily fixed setting the timezone to UTC before the compression happens). In some cases the compressed files are generated during the build, and thus add build times in the metadata of compressed files (in this case the creation date of the files needs to be normalized somehow). 

As explained in my [application](https://wiki.debian.org/SummerOfCode2015/StudentApplications/EduardSanou), I finished exams on the end of June, that's why I chose to work on small fixes first, so that I could make the most out of my time between studying and finishing university projects and reports.
I'm happy with my first month, as I have worked as originally planned. Actually, my estimation of the number of bugs I could submit every week was surpassed in reality!

## Second month

Once the university was over, I started dedicating myself fully to the project. This allowed me to start working on toolchain fixes, following my original plan on working with timestamp related issues.

In particular I have been working a lot in implementing a [proposal for deterministic timestamps](https://wiki.debian.org/ReproducibleBuilds/TimestampsProposal) that appeared in the reproducible builds project. The idea is to define an environment variable called `SOURCE_DATE_EPOCH` that contains a known timestamp in Unix epoch format. With this variable exported, tools that would embed the localtime in their generated or processed files, can use this externally supplied date. This would happen only if `SOURCE_DATE_EPOCH` is exported, so the behaviour of the tool wouldn't change if the variable is not set. 

The first package I patched to implement this behaviour was [gcc](https://gcc.gnu.org/ml/gcc-patches/2015-06/msg02210.html). The reason behind this is that there are about 420 unreproducible packages due to using the `__DATE__`, `__TIME__` and `__TIMESTAMP__` C macros. My patch changes the behavior of the macros `__DATE__` and `__TIME__` if `SOURCE_DATE_EPOCH` is exported. I submitted this patch to the gcc-patches list. Even though there was some interesting discussions in the list, the patch has not been accepted yet. Seeing how the reproducible builds idea is gaining momentum and becoming widespread, I'm positive that at some point the gcc people will be more receptive for such patch.

The second work with `SOURCE_DATE_EPOCH` was in [debhelper](https://bugs.debian.org/791823); I patched this building tool to export the variable with the latest debian/changelog entry timestamp. With this patch, all the tools that run under dh will be able to use it to embed deterministic timestamps. Unfortunately some parts of the build process of some packages don't happen under debhelper, so the variable needs to be exported in a different way.

Having submitted the debhelper patch allowed many packages to become reproducible after the tools that embedded timestamps were patched to honour `SOURCE_DATE_EPOCH`. As of today, the toolchain packages I have patched to do that are: [gcc](https://gcc.gnu.org/ml/gcc-patches/2015-06/msg02210.html), [libxslt](https://bugs.debian.org/791815), [gettext](https://bugs.debian.org/792687), [ghostscript](https://bugs.debian.org/794004) and [qt4-x11 (qhelpgenerator)](https://bugs.debian.org/794681).

I have also continued working on fixing individual packages affected by timestamps, random orderings (such as the ones from listing hash keys) and locale depending orderings; I have tagged packages in our infrastructure to note what kind of issue makes them unreproducible; I have updated some parts of the [Reproducible Builds Wiki](https://wiki.debian.org/ReproducibleBuilds).

# Impressions about reproducible builds

The work I did during the first month felt a bit tedious sometimes: it didn't require much creativity or thinking as most of the fixes where quite mechanical, following a recipe. After I became free from university duties, I started looking into less trivial issues, which require more deep investigation and feel more rewarding once they are fixed. I also worked on toolchain fixes, which need more work and need more care. Fixing toolchain packages feels particularly rewarding because they can cause many packages to become reproducible at once.

There is a very active community in the reproducible builds project! It's great to see so many people contributing to this project spending so many hours and putting so much effort. I've felt very welcome from the beginning and I have gotten kind replies and helpful answers to all the questions and doubts I've had, both from my mentor and from the other people in the project.

I want to add that I'm still amazed by the awesome infrastructure set up for the reproducible builds project. The team is using a Jenkins machine to continuously build packages to check for reproducibility, with irc notifications for changes, and also with a really useful web interface to list all the packages organized by issues that allows exploring them individually with all the available information. Also not only the infrastructure is used to build Debian amd64 packages, but also FreeBSD, NetBSD, [OpenWRT](https://reproducible.debian.net/openwrt/openwrt.html), [coreboot](https://reproducible.debian.net/coreboot/coreboot.html) and lately Debian armhf with the help of a few new arm nodes. 

# Impressions about working on a free software project

This was my first time working on a community driven free software project and I've learned so many things.

Something I learned during the first days, which is even more present in such wide project like the reproducible builds, is that contributing is not just writing patches for the features you want; you also need to convince the maintainer of the package to accept the patch! I was a bit surprised at the beginning because even if this is a Debian project, that aims to make changes to the whole distribution, decisions are not absolute for the whole Debian project. After taking decisions within the reproducible builds teams on how to approach things, we need to convince the rest of the Debian developers (mainly maintainers) to follow them, as they are allowed to disagree. So it is required to work together for solutions that makes everyone comfortable, usually with discussions on mailing lists or irc.

There is another fact that I wasn't expecting before getting involved in this project. The kind of teamwork I have done previously involves having a leader who decides how stuff is done, who takes decisions when needed and oversees the whole project. There seems to be a different philosophy in Debian. Instead of having a leader, everyone tries their best, trying to convince the others that their solution is good, often by showing an implementation of the solution and providing proof that it works, rather than trying to get the solution accepted before coding it. Also, solutions and ideas are valued for their quality rather than by the position of the person submitting them, and there is no hierarchy within the group: all comments and advices are taken equally, valuing their usefulness regardless of who gives them.

Usually there are no votes when deciding things. Members try their best on their approaches, trying to convince others as best as they can. And even if someone disagrees they may end up accepting the solution if they don't manage to convince the original proposer of doing things differently. The idea is to spend more time working and coding than arguing and deciding on the way to do things. So far I've seen this approach to be very efficient :)

I've been told by my mentor that for difficult cases there exist a [Debian committee](https://www.debian.org/devel/tech-ctte) that helps mediate on disagreements, but that is only used as a last option, probably when the discussion gets heated up.

## Personal experience

Overall I'm very happy to finally having set my foot in the free software community, where I'm able to contribute to the kind of software I have been using for years. The sense of community in Debian is really big, and everyone is invited to participate. 

I think that Google is doing an awesome job with the Google Summer of Code, not only because it gives a lot to free software but because it helps students to join the free software world as contributors (which is something that may be difficult to get into when you don't know how to begin, as it happened to myself for some time). I plan to continue contributing to the free software world, and I'd encourage anyone to find projects to get involved and contribute as well!

Happy hacking to everyone!
