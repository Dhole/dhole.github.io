+++
Categories = ["stm32f4", "gameboy", "rust"]
date = "2018-02-23T16:33:57+01:00"
title = "Writing GameBoy Chinese cartridges with an STM32F4"
draft = true
+++

Things I learned: 

- While DMA is transfering from USART to RAM, the CPU can't access RAM, so I wonder if my asynchronous design has any benefit (while it clearly adds a lot of complexity).

- How to set up USART DMA

- There's one particular GPIO that can't be used because it's connected to the external clock source.  Took me a while to figure out!

