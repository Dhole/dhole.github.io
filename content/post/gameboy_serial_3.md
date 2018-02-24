+++
Categories = ["stm32f4", "gameboy", "rust"]
date = "2018-02-25T16:33:57+01:00"
title = "Printing on the GameBoy Printer using an STM32F4"
draft = true

+++

Things I learned: 

- While DMA is transfering from USART to RAM, the CPU can't access RAM, so I wonder if my asynchronous design has any benefit (while it clearly adds a lot of complexity).

- How to set up USART DMA

- How to set up timer at a particular frequency

- There's one particular GPIO that can't be used because it's connected to the external clock source.  Took me a while to figure out!

{{% img1000 src="../../media/gameboy_serial/Sigint_112_www.mikrocontroller.net_1.jpg" caption="Oscilloscope capture by Sigint 112 posted at [www.microcontroller.net](http://www.mikrocontroller.net/topic/87532)" %}}
{{% img1000 src="../../media/gameboy_serial/Marat_Fayzullin_fms.komkon.org.gif" caption="Game Link serial protocol by [Marat Fayzullin](https://fms.komkon.org/GameBoy/Tech/Hardware.html)" %}}
