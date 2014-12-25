+++
Categories = ["stm32f4", "gameboy"]
date = "2014-12-25T01:35:42+01:00"
title = "Booting the GameBoy with a custom logo"

+++

With the cartridge emulator implemented on an STM32F4 we can do some cool stuff.
For example, we can make the GameBoy boot with our own custom logo! 

# Bootstrap ROM

When the GameBoy boots, an intenral Bootstrap ROM is mapped to the beginning of the 
memory and execution begins. This bios is in charge of initializing the hardware
as well as scrolling the Nintendo logo and checking that the cartridge i valid.
The logo shown on screen is actually read from the cartridge, that's the reason
why a black rectangle appears when no cartridge is inserted, or garbage appears
when the cartridge pins fail. If the Nintendo logo doesn't match the copy stored
in the bios, the GameBoy locks itself. But there is a trick we can do! The
GameBoy reads the logo from the cartridge two times, the first one to draw it
on screen and the second one to check if it's valid. We can thus send first a
custom logo and later the original one in order to let the GameBoy boot properly.

More on the GameBoy Bootstrap ROM can be read at [GBdevWiki](http://gbdev.gg8.se/wiki/articles/Gameboy_Bootstrap_ROM)

# Code

In order to achieve this we can modify the read function of our cartridge emulator
to the following:

The `no_show_logo` flag is false at boot, and allows the first logo read (stored
from 0x104 to 0x133) to be done on a custom array. Once the last byte has been
read, the flag is set to true so that the following reads are performed to the
real rom.

{{% gist Dhole/a097cee60b990f65d869 %}}

## Custom logo creation

In order to create custom logos I wrote two python scripts:
- [draw_logo.py](https://github.com/Dhole/stm32f_GBCart/blob/master/draw_logo.py): Draws a logo on a window
- [make_logo.py](https://github.com/Dhole/stm32f_GBCart/blob/master/make_logo.py): Converts a png logo image into a binary file to be used as a boot logo

The logo is stored in binary form inside the cartridge with a binary representation:
Set bits represent a black pixel and unset bits represent a white pixel. The logo is
stored in blocks of 4x4, first filling the top part and later filling the bottom part.
The way the pixels are stored can be understood better by looking at `draw_logo.py`.

`make_logo.py` allows you to convert a 48x8 pixel black and white png image to a
binary logo to be used by the cart emulator

# Results

I have drawn the following logo to be used at boot:

{{% img src="/media/gameboy_stm32f4/dhole_logo.png" caption="Custom logo featuring my nickname and a cute Dhole" %}}

{{% youtube aVxJXK9QvPk %}}

Booting with the custom logo, running Dr Mario.

{{% youtube OPYkzv217P4 %}}

Booting with the custom logo, running the demo Skinke by Jumalauta.
