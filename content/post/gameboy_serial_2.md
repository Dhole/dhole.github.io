+++
Categories = ["stm32f4", "gameboy", "rust"]
date = "2018-02-23T16:33:57+01:00"
title = "Virtual GameBoy Printer with an STM32F4"

+++

In this second part of the project about interfacing the GameBoy serial communication with an embedded development board I will explain how I built a Virtual GameBoy Printer.  The embedded board will be simulating a real GameBoy Printer, replying to the GameBoy following the protocol used by the GameBoy Printer so that the GameBoy sends the entire data meant to be print.  This data will then be forwarded to my computer which will construct a png image out of it.

# GameBoy Printer protocol

The first step for this part of the project is understanding how the GameBoy Printer protocol works so that we can interpret the commands the GameBoy sends to it.  In the first part of the project I posted a [capture of the data transferred to the GameBoy Printer by the GameBoy Camera to print a photo](../../media/gameboy_serial/printer.txt).  This will be useful to verify that we understand how each command should look like.

Thankfully, we won't need to be reverse engineering the protocol (a task that should be doable with the sniffer we built in the first part) because it is well documented online.  My main sources of information were [Furrtek's website](http://furrtek.free.fr/?a=gbprinter&i=2) and the [GameBoy Printer entry at Wikipedia](https://en.wikipedia.org/wiki/Game_Boy_Printer).

I will summarize the protocol here, but bear in mind that I'm not adding new information, I'm just merging the information from Furrtek's website and the Wikipedia entry.

In the GameBoy Printer protocol, the GameBoy will act as master and the Printer as slave.  All the communications start with a command sent from the GameBoy and end with a reply from the Printer (which consists of an acknowledgement and a status code).

## Packet Format

The command format consists of a header, a variable length payload (`DATA` of length `LEN`) and a checksum.  The following table shows the complete packet format along with the reply:

```
Byte    |  0   |  1   |  2  |  3   | 4 | 5 |  6   | 6+LEN | 6+LEN+1 | 6+LEN+2 | 6+LEN+3
--------|------|------|-----|------|---|---|------|-------|---------|---------|---------
GameBoy | MAGIC_BYTES | CMD | ARG0 |  LEN  | DATA |   CHECKSUM      |         |
Printer |      |      |     |      |   |   |      |       |         |   ACK   | STATUS

MAGIC_BYTES := 0x88 0x33
ACK := 0x81
```

16 bit values (`LEN` and `CHECKSUM`) are sent in little-endian format (low byte first, high byte second).

The `CHECKSUM` is the 16 bit integer value that is obtained by summing all the packet bytes except for the `MAGIC_BYTES` and the `CHECKSUM` itself.

The following picture shows the beginning of a packet captured with an oscilloscope.

{{% img1000 src="../../media/gameboy_serial/furrtek_printer_protocol.png" caption="GameBoy Printer serial communication capture by [Furrtek](http://furrtek.free.fr/?a=gbprinter&i=2)" %}}

## Commands

### **Initialize** (`CMD = 0x01, DATA = {}`)

This command is sent before sending data to be printed, it prepares the Printer to start receiving data.

### **Print** (`CMD = 0x02, LEN = 4, DATA = PRINT_OPTS`)

This command is sent after some data has ben transmitted and starts the printing process of the previously transmited data.  `PRINT_OPTS` specifies some printing options:

```
Byte          |  0   |    1    |    2    |    3
--------------|------|---------|---------|----------
typical value | 0x01 |  0x13   |  0xE4   |   0x40
meaning       |   ?  | MARGINS | PALETTE | EXPOSURE

MARGINS: High nibble is margin before printing, low nibble is margin after printing.
PALETTE: Color palette following the GameBoy palette representation:
    
    Bit   |  0,1  |     2,3    |    4,5    |  6,7 
    ------|-------|------------|-----------|-------
    Color | White | Light Gray | Dark Gray | Black

EXPOSURE: Color exposure as a 7 bit value
```

### **Send data** (`CMD = 0x04, LEN = 640, DATA = GB_TILES`)

This command is used to send the data to be printed in batches of two rows of 20 GameBoy tiles, which require 640 bytes.  Each tile is an 8x8 pixels image using 4 grayscale tones, and require 8x8x2 = 32 bits.  Since the GameBoy has a 160x144 pixels display, 20 tiles will create a row of (20x8)x8 = 160x8 pixels (320 bytes).

The tile pixels are stored by rows, where each row is stored as 2 bytes.  For every row, the first byte represents the less significant bits of the 2-bit tone pixels and the second byte represents the most significant bits.  The following example shows how 2 bytes are decoded into a 2-bit tone pixel row:

```
1st byte: 00110011 ---->  00112233
2nd byte: 00001111 --'
```

In order to print an image corresponding to the GameBoy screen, 18 tile rows are required, which means that this command will be called 9 times.  This is the way the GameBoy Camera prints.  If you'd like to print images higher than 144 pixels, you can combine several images and print them independently leaving a 0-length margin in between.

### **Query status** (`CMD = 0x0F, DATA = {}`)

This command queries the current status of the Printer.  It is commonly used after the print command to check when the Printer has finished printing.

## Status codes

The status code is a byte where each bit, if set, indicates the following:

```
Bit 0: Checksum Error
Bit 1: Printer Busy (printing)
Bit 2: Image Data Full
Bit 3: Unprocessed Data
Bit 4: Packet Error
Bit 5: Paper Jam
Bit 6: Other Error
Bit 7: Battery Too Low
```

More than one bit can be set at the same time.

## Wrap up

A 160x144 pixels image is commonly printed issuing the following commands: 

- Initialize
- Loop until all data is sent:
    - Send data
    - Query status for any error
- Send data with empty payload
- Print
- Loop until the GameBoy printer is no longer busy:
    - Query status

If a Send data with empty payload is not sent after the tile data has been sent and before the Print command, the GameBoy Printer will not print and instead return an error!

# Implementation

## NUCLEO-F411RE side

The connection of the Game Link Cable to the NUCLEO will be the same as in the first part of the project.  The GPIO setup will be the same except for the `SIN` pin, which will be configured as output (so that we can reply to the GameBoy simulating a GameBoy Printer).  Unlike in the first part, we setup the interrupt to trigger both then the `SCK` signal goes low (to output the sending bit) and when the `SCK` signal goes high (to read the receiving bit).

{{< highlight C >}}
static void
gblink_slave_gpio_setup(void)
{
	// PA0 -> SCK
	gpio_mode_setup(GPIOP_SCK, GPIO_MODE_INPUT, GPIO_PUPD_NONE, GPION_SCK);
	// PC0 -> SIN
	gpio_mode_setup(GPIOP_SIN, GPIO_MODE_OUTPUT, GPIO_PUPD_PULLDOWN, GPION_SIN);
	gpio_set_output_options(GPIOP_SIN, GPIO_OTYPE_PP, GPIO_OSPEED_100MHZ, GPION_SIN);
	gpio_clear(GPIOP_SIN, GPION_SIN);
	// PC1 -> SOUT
	gpio_mode_setup(GPIOP_SOUT, GPIO_MODE_INPUT, GPIO_PUPD_NONE, GPION_SOUT);

	nvic_set_priority(NVIC_EXTI0_IRQ, 0);
	nvic_enable_irq(NVIC_EXTI0_IRQ);

	exti_select_source(EXTI0, GPIOP_SCK);
	exti_set_trigger(EXTI0, EXTI_TRIGGER_BOTH);
	exti_enable_request(EXTI0);
}
{{< /highlight >}}

Now that we have a way to receive and send serial bytes, we need to simulate a GameBoy Printer.  In order to do so I have implemented a state machine that simulates the GameBoy Printer on the NUCLEO, but it's a simplified one: it always replies with the same status where all bits are cleared.  The GameBoy will be fine with these replies, and will think that all the data is being received correctly and printed instantly.  While doing this, the NUCLEO will be sending all the bytes received from the GameBoy over USART to my computer.

The interrupt handler now looks like this:

{{< highlight C >}}
inline static void
exti0_isr(void)
{
	exti_reset_request(EXTI0);

	if (gpio_get(GPIOP_SCK, GPION_SCK) == 0) { // FALLING
		gb_sout |= gpio_get(GPIOP_SOUT, GPION_SOUT) ? 1 : 0;
		gb_bit++;

		if (gb_bit == 8) {
			// Send gb_sout over USART2
			usart_send_blocking(USART2, gb_sout);

                        printer_state_update(gb_sout);
                        switch (printer_state) {
                        case ACK:
                                buf_push(&recv_buf, 0x81);
                                break;
                        case STATUS:
                                buf_push(&recv_buf, 0x00);
                                break;
                        default:
                                break;
                        }

			// Reset state
			gb_bit = 0;
			gb_sout = 0;

			// Prepare next gb_sin
			if (buf_empty(&recv_buf)) {
				gb_sin = 0x00;
			} else {
				gb_sin = buf_pop(&recv_buf);
			}
		} else {
			gb_sin <<= 1;
			gb_sout <<= 1;
		}
	} else { // RISING
		(gb_sin & 0x80) ? gpio_set(GPIOP_SIN, GPION_SIN) : gpio_clear(GPIOP_SIN, GPION_SIN);
	}
}
{{< /highlight >}}

The following snippet shows how the state machine is implemented and how the transitions work.  Implementing the state machine is required because the commands sent by the GameBoy have a variable length payload, and the GameBoy Printer is required to reply with an ACK at the precise end of the command packet.

{{< highlight C >}}
const char printer_magic[] = {0x88, 0x33};

enum printer_state {MAGIC0, MAGIC1, CMD, ARG0, LEN_LOW, LEN_HIGH, DATA, CHECKSUM0, CHECKSUM1, ACK, STATUS};
enum printer_state printer_state;
enum printer_state printer_state_prev;
uint16_t printer_data_len;

static void
printer_state_update(uint8_t b)
{
	printer_state_prev = printer_state;
	switch (printer_state) {
	case MAGIC0:
		if (b == printer_magic[0]) {
			printer_state = MAGIC1;
		}
		break;
	case MAGIC1:
		if (b == printer_magic[1]) {
			printer_state = CMD;
		} else {
			printer_state = MAGIC0;
		}
		break;
	case CMD:
		printer_state = ARG0;
		break;
	case ARG0:
		printer_state = LEN_LOW;
		break;
	case LEN_LOW:
		printer_data_len = b;
		printer_state = LEN_HIGH;
		break;
	case LEN_HIGH:
		printer_data_len |= b << 8;
		if (printer_data_len != 0) {
			printer_state = DATA;
		} else {
			printer_state = CHECKSUM0;
		}
		break;
	case DATA:
		printer_data_len--;
		printer_state = (printer_data_len == 0) ? CHECKSUM0 : DATA;
		break;
	case CHECKSUM0:
		printer_state = CHECKSUM1;
		break;
	case CHECKSUM1:
		printer_state = ACK;
		break;
	case ACK:
		printer_state = STATUS;
		break;
	case STATUS:
		printer_state = MAGIC0;
		break;
	}
}

static void
printer_state_reset(void)
{
	printer_data_len = 0;
	printer_state = MAGIC0;
	printer_state_prev = printer_state;
}
{{< /highlight >}}


## Computer side

On the computer side, we will be receiving all the data the GameBoy is sending to the virtual printer.  We will need to parse the packets, extract the tile data and reconstruct the images so that we can visualize and store them.  As in the previous part, I'll be using Rust, reusing the same code to interface with the serial port as in part one.  To store the image as a PNG I will use the [Rust image crate from the Piston project](https://github.com/PistonDevelopers/image).

The code will run in a loop waiting for the magic bytes and parse the following bytes to make a packet.  If the packet is a Send data command, the tile rows will be appended to a vector called `tile_rows`.  If the packet is an Init command, the `tile_rows` vector will be cleared.  Finally, if the packet is a Print command, the `tile_rows` vector will be decoded into a matrix that will be stored as a PNG image.  This will allow us to send (or virtually print) multiple pictures from the GameBoy to the computer on the same run of the program.

The following code shows this behaviour.  I've ommited some constants and enum declarations that encode the different protocol values:

{{< highlight rust >}}
fn mode_printer<T: SerialPort>(mut port: &mut BufStream<T>) -> Result<(), io::Error> {
    let mut tile_rows = Vec::<Vec<u8>>::new();
    loop {
        // Wait for the magic bytes.
        try!(read_until_magic(&mut port, &PRINT_MAGIC));
        let mut buf = vec![0; 4];
        // Read cmd, arg1, len_low, len_high
        try!(port.read_exact(&mut buf));
        let cmd = buf[0];
        let args = &buf[1..4];
        let len = (args[1] as u16) + ((args[2] as u16) << 8);
        let mut payload = vec![0; len as usize];
        let mut checksum = vec![0; 2];
        try!(port.read_exact(&mut payload));
        try!(port.read_exact(&mut checksum));
        match PrintCommand::from_u8(cmd) {
            Some(PrintCommand::Init) => {
                println!("Receiving data...");
                tile_rows.clear();
            }
            Some(PrintCommand::Print) => {
                let palette = &payload[2];
                let filename = format!(
                    "gb_printer_{}.png",
                    time::now().strftime("%FT%H%M%S").unwrap()
                );
                println!("Saving image at {}", filename);
                try!(printer_save_image(&tile_rows, palette, filename));
            }
            Some(PrintCommand::Data) => {
                if len != 0 {
                    tile_rows.push(payload);
                }
            }
            Some(PrintCommand::Status) => {}
            None => {}
        }
        let mut ack_status = vec![0; 2];
        try!(port.read_exact(&mut ack_status));
    }
}
{{< /highlight >}}

The function `printer_save_image` will decode the tile rows into a matrix so that the image can be saved as a grayscale PNG.  The helper function `tile_row_to_pixel_rows` decodes a single tile row into 'pixel rows', that is 8 rows of 160 grayscale pixels each.

{{< highlight rust >}}
fn printer_save_image(
    tile_rows: &Vec<Vec<u8>>,
    palette_byte: &u8,
    filename: String,
) -> Result<(), io::Error> {
    let palette: Vec<u8> = BitVec::from_bytes(&[*palette_byte])
        .iter()
        .tuples()
        .map(|(h, l)| (l as u8) + 2 * (h as u8))
        .map(|v| v * (255 / 3))
        .collect();
    let mut img = ImageBuffer::new(160, 16 * tile_rows.len() as u32);
    img.put_pixel(0, 0, image::Luma([255u8]));

    let mut pixel_rows = Vec::new();
    for tile_row in tile_rows {
        let (tile_row_a, tile_row_b) = tile_row.split_at(tile_row.len() / 2 as usize);
        let mut pixel_rows_a = tile_row_to_pixel_rows(tile_row_a);
        let mut pixel_rows_b = tile_row_to_pixel_rows(tile_row_b);
        pixel_rows.append(&mut pixel_rows_a);
        pixel_rows.append(&mut pixel_rows_b);
    }

    for (y, pixel_row) in pixel_rows.iter().enumerate() {
        for (x, val) in pixel_row.iter().enumerate() {
            img.put_pixel(x as u32, y as u32, image::Luma([palette[*val as usize]]));
        }
    }

    img.save(&Path::new(&filename))?;
    return Ok(());
}

fn tile_row_to_pixel_rows(tile_row: &[u8]) -> Vec<Vec<u8>> {
    let mut pixel_rows: Vec<Vec<u8>> = (0..8).map(|_| vec![0u8; 160]).collect();
    for i in 0..(tile_row.len() / 16 as usize) {
        let tile = &tile_row[i * 16..i * 16 + 16];
        for j in 0..8 {
            let tile_pixel_row = BitVec::from_bytes(&[tile[j * 2]])
                .iter()
                .zip(BitVec::from_bytes(&[tile[j * 2 + 1]]).iter())
                .map(|(l, h)| (l as u8) + 2 * (h as u8))
                .collect::<Vec<u8>>();
            for k in 0..8 {
                pixel_rows[j][i * 8 + k] = tile_pixel_row[k];
            }
        }
    }
    return pixel_rows;
}
{{< /highlight >}}

# Result

And finally, the result:

{{% img1000 src="../../media/gameboy_serial/gb_printer_2017-09-02T165217.png" caption="Picture taken with a GameBoy Camera and transferred to my computer using the virtual printer" %}}

To see the full source code of this project, check out the following repositories:

- [gb-link-stm32f411: the code that runs on the NUCLEO-F411RE](https://github.com/Dhole/gb-link-stm32f411)
- [gb-link-host: the code that runs on the computer](https://github.com/Dhole/gb-link-host)

The source code contains the three parts of the project joined into a single code base.

And this concludes the second part of the project.  Stay tunned for the third part, where I'll do the reverse of this part: print from my computer on a real GameBoy Printer.
