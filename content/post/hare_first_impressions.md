---
title: "First impressions on Hare language"
date: 2024-01-20T14:45:38+01:00
draft: true
Categories: ["chip8", "hare"]
---

# Introduction

[Hare is a new programming language](https://harelang.org/) that was [announced
in 2022](https://harelang.org/blog/2022-04-25-announcing-hare/) and which was
started by [Drew DeValut](https://drewdevault.com/).  It's currently being
developed openly by a community of contributors.  Here's a description of the
language from the official website:
> Hare is a systems programming language designed to be simple, stable, and
> robust. Hare uses a static type system, manual memory management, and a
> minimal runtime. It is well-suited to writing operating systems, system
> tools, compilers, networking software, and other low-level, high performance
> tasks. 

I enjoy learning about new programming languages, and I'm personally attracted
to the effort of reducing complexity in software and creating simple designs,
goals that Hare itself tries to achieve.  With this, I decided to learn Hare
and try it; and I'm going to share my experience through this process in
this post.

# My first Hare project

A long time ago I became interested in learning how emulators work, so I looked
at the simplest machine I could find to write an emulator for it.  I discovered
the Chip8, a very simple 8 bit Virtual Machine made for videogames in the 70s.
I implemented an [emulator for it in C++](https://github.com/Dhole/Chip8-emu).
That was in fact my first emulator!  Please don't judge the code quality of
that implementation, I wrote it 11 years ago and I didn't have a lot of
software engineering experience by then.

Since the implementation of the Chip8 emulator is very simple, I've been
re-implementing it (or porting it) to new languages that I learn as a way of
practicing the new language.

Here you can find the [Hare implementation of my Chip8
emulator](https://github.com/Dhole/chip8-ha/).  The main two files are:
- [chip8/chip8.ha](https://github.com/Dhole/chip8-ha/blob/main/chip8/chip8.ha): Contains the platform-agnostic (or backend) Chip8 emulator implementation
- [src/main.ha](https://github.com/Dhole/chip8-ha/blob/main/src/main.ha):
  Contains the frontend using the [SDL2 library](https://www.libsdl.org/) to
  handle keyboard inputs, window and frame rendering and audio.

To use the SDL2 library I initially tried the [`~sircmpwn/hare-sdl2` wrapper
library](https://git.sr.ht/~sircmpwn/hare-sdl2/tree).  I had to patch it in
order to correctly setup the [texture pixel
format](https://lists.sr.ht/~sircmpwn/hare-dev/patches/48378), and got
everything working except for sound.  At that point I realized that the
wrappers for the sound API were not done, and I found this other attempt in
[`~spxtr/hare-sdl2`](https://git.sr.ht/~spxtr/hare-sdl2) which was more
complete: it had the audio API wrappers, and only needed the texture pixel
format enum for my needs.  Since I needed some changes from it, I [forked it
here](https://github.com/Dhole/hare-sdl2).

The implementation is currently complete and works as expected.

# Personal impressions

In this section I will explain some points I liked and some I didn't like about
Hare. This could be treated as feedback, but bear in mind that some these
impressions are very subjective.

## Positive

### Nullable types

This small feature can remove memory a common bug in C; where a function
returns a pointer with a small chance of failing.  On failure a null pointer
would be returned.  If the caller doesn't check for null pointer, a null
de-reference may happen.  Having nullable types forces the caller to check for
the null pointer case before de-referencing.

### Sum types / tagged unions

Making a new type out of a collection of types, with ways to check which type
is instantiated.  This works great for having functions that can return a
result or an error, or in general for functions that may receive/return
different kinds of data.

### Slices

Having slice semantics adds a lot of flexibility for very common operations.
Also having a native representation of a consecutive list of elements which
also stores the length helps greatly on simplifying APIs and removing invalid
memory accesses when indexing.

### Nice standard library

I see that a lot of effort has been put into having a very nice standard
library.  Although this is not part of the language spec, I consider it very
important as part of the language as a whole (perhaps seeing the language as
the entire ecosystem).  I find it impressive that a language so young has a
standard library this extensive.

### `!` and `?` operators

The `!` operator allows extracting the non-error value of a function return
value or abort in the case of error.  This is very convenient for errors that
we believe won't happen, or for errors that we don't want to recover from.

The `?` operator works similarly, but instead of aborting causes the function
to return the error, to be dealt by the caller.

### Small boring language

Here the usage of "boring" is used in a positive sense, similar to the term
[Boring Crypto coined by Daniel J.
Bernstein](https://cr.yp.to/talks/2015.10.05/slides-djb-20151005-a4.pdf).  Hare
is a language that is easy to learn and doesn't offer any surprise.  It tries
to follow simple patterns that are known to work well and are commonly used,
and avoids others that may be more complex and may be more niche. 

## Negative

### No dot method syntax

I'm very used to modeling many problems in code following the convention of
Objects with associated methods.  This modeling is seen in Object Oriented
languages, but also in modern languages like Go, Rust or Zig, which don't
follow Object Orientation patterns to the full extent.  I find that the syntax
`object.method()` leads to cleaner code, and even when the language doesn't
support this syntax, the pattern is still used.

As an example, in my Chip8 implementation, once the chip8 object has been
created as `c8` I use this to load a rom: `chip8::load_rom(&c8,
rom[..rom_size])`; In dot method syntax it would look like
`c8.load_rom(rom[..rom_size])`.

Another example is the hare API of the SDL2 wrapper.  An idiomatic API for SDL2
may look like this:
```hare
sdl::set_render_draw_color(render, 0, 0, 0, 255)?;
sdl::render_clear(render)?;
sdl::render_present(render);
```
Whereas dot method syntax could look like this:
```
render.set_draw_color(0, 0, 0, 255)?;
render.clear()?;
render.present();
```

On the other hand, this is how code that works with objects looks like in C;
and I believe I could get used to it.

### Pointer arithmetic

I'm not sure if I missed a better way to perform pointer arithmetic, but I
ended up with quite ugly code.  I believe pointer arithmetic has two big use
cases: working with low level code that accesses memory directly, and
interfacing with other languages like C.  In my case, I encountered the need
for pointer arithmetic when interacting with the SDL library: to play audio I
needed to implement a callback function that receives a pointer to memory that
I need to fill with samples.  The audio can be configured with different sample
formats (that use different sizes), so the callback interface needs to be
generic.  It looks like this: 
```hare
fn(userdata: nullable *opaque, stream: *u8, len_: int)
```
Where `steram` is a pointer to the memory where I should write my samples,
which are `f32` in my case.  I ended up with the following code to write a
value at offset `i`:
```hare
*((stream: uintptr + i: uintptr * size(f32)): *f32) = v;
```

If you know of a more ergonomic way to do this, please let me know!

I can imagine two solutions for this:

A) Support a simpler way to perform pointer arithmetic, for example by allowing
arithmetic operations on reference types like this:
```
*(stream: *f32 + i: *f32)
```

B) Introduce a way to create a slice from raw parts like this:
```
let stream_slice = slice_from_raw(stream: *f32, len_ / size(f32));
stream_slice[i] = v;
```

### Type casting inconsistency

I think this is following how C works, which is not ideal.  Type casting can
sometimes convert the type, and other types just reinterpret the bytes
underlying the variable as another type, without any conversion.  Here's a
sample code:

```hare
use fmt;

type a = struct {
	x: f32
};

type b = struct {
	x: u32
};

type c = struct {
	x: u32,
	y: u32,
};

export fn main() void = {
	let x: f32 = 1.0;
	let y = x: u32;
	fmt::printfln("{}", y)!;
	let x = a { x = 1.0 };
	let y = &x: *b;
	fmt::printfln("{}", y.x)!;
	let z = y: *c;
	fmt::printfln("{}", z.y)!;
};
```

The previous code outputs this on my machine:
```hare
1
1065353216
32766
```

Let's think about what's going on:
- The first output is `1`.  We crated a `1.0f32` and converted it into `u32`.
  The byte layout of `1.0f32` is different than `1.0u32`, and here Hare takes
  the integer part and converts it into `u32`.
- The second output is `1065353216`.  This is taking the byte representation of
  `1.0f32` and interpreting it as `u32`, without doing a conversion, so we get
  an unexpected result.
- The third output is `32766` (and I actually get different values after
  executing the program multiple times).  We're reading memory that past the
  original struct.

The first case seems safe (as long as we're aware about the lossy conversion)
and expected; I also imagine this kind of casting to happen regularly in the
code, and that should be OK.

The second case seems safe (we're not violating memory safety) although the
result is probably unexpected.  I think this use case is quite uncommon and
needs to be reviewed with special care.

The third case is unsafe because we're accessing memory outside of the bound of
the original variable we're referencing.  There can be use cases for this.

My main point is that both three cases look the same in the code, but two of
them can be quite dangerous.  I prefer languages that have special semantics
for dangerous stuff.  For example, in Rust the first case would be [casting
like this: `x as
u32`](https://doc.rust-lang.org/rust-by-example/types/cast.html), whereas the
other cases would require using [`mem::transmute` which requires an `unsafe`
block](https://doc.rust-lang.org/std/mem/fn.transmute.html).  In Zig, the first
case would be done with
[coercion](https://ziglang.org/documentation/master/#Type-Coercion), and the
other ones with [explicit builtin cast
functions](https://ziglang.org/documentation/master/#Explicit-Casts)

### General feeling of unsafety

While Hare improves some of the safety issues of C (for example, by doing bound
checks on array/slice indexing), it still leaves the door open for many kinds
of memory safety bugs (and also memory leaks).  All the memory is managed
manually so we could have situations like:
- Allocating an object and forgetting to free it, leading to a memory leak.
  This is not a memory safety issue, but memory leaks are very annoying.
- Freeing an object that is still referenced somewhere, and then de-referencing
  it, leading to undefined behavior.
- ~~Double frees.  Freeing an object that has already been freed, possibly
  corrupting metadata from the allocator~~.  This is currently being detected
  by the allocator.
- Reference to an element of an object that becomes invalidated by another
  reference to that object.  This is the case of having a pointer to a slice,
  which becomes invalid after we grow the slice causing a reallocation.

This point applies equally to Zig.  After having used memory safe languages
I've really appreciated not having to deal with these kind of issues.  On the
other hand, I understand that one of the goals of Hare is to be a simple and
small system language; I wonder if such a goal can be achieved while adding
memory safety to the language.

# Implementation status

The current implementation of the compiler is incomplete.  For example, there's
no check to make sure that the branches of a match clause are exhaustive.  The
following code demonstrates this: function `foo` can return `x`, `y` or `z`, but
the `match` only handles cases `x` and `y`.

```hare
use fmt;

type x = struct { x: int };
type y = struct { y: int };
type z = struct { z: int };

export fn main() void = {
	match(foo()) {
	case let v: x => fmt::printfln("{}", v.x)!;
	case let v: y => fmt::printfln("{}", v.y)!;
	};
};

fn foo() (x | y | z) = {
	return z{ z = 0 };
};
```

This snippet compiles but aborts with the following message:
```
Abort: main.ha:8:14: execution reached unreachable code (compiler bug)
```

I remember reading somewhere (maybe on a public message from a Hare developer)
that this feature was missing.  Nevertheless the execution doesn't lead to
undefined behavior, as the compiler emits a guard to abort the execution in a
controlled manner when the case is not covered.

I'm not sure how many cases like this exist, but this is expected from a
language at this phase; you just need to be aware of this.

# Closing thoughts

Overall I find Hare an interesting language.  I think it successfully fulfills
the goals of being simple and minimal, and improves C in many ways without
growing in complexity.  Having an alternative language to C that improves it,
is still good in the same domains that C is (system's programming language),
and doesn't growing in complexity (both language and implementation) is a very
appealing to me.  I think many would agree with this; but perhaps the hardest
part to agree is how we define "improvement", as different people may have
different priorities.  I can't help but desire improvements in memory safety,
and to me Hare doesn't fully scratch this itch; on the other hand, I'm not sure
how far you can go in memory safety without growing in complexity while staying
useful in the same domain as C.

I think I will keep exploring Hare a bit more, in particular I plan to take a
look at [AresOS](https://ares-os.org/), a  microkernel operating system written
in Hare.
