# obsidian [![Tek-OSS](https://tektronix.github.io/media/TEK-opensource_badge.svg)](https://github.com/tektronix)

Displays Jenkins build status with a string of RGB LED

## Maintainer

-   [Hong Quach](https://github.com/htquach)

## BOM

1.  A Raspberry Pi with Raspbian OS
    -   CanaKit Raspberry Pi 3 B+ (B Plus) with Premium Clear Case and 2.5A Power Supply
    -   A microSD card for the Raspberry Pi to run the Raspbian OS

2.  WS2812B addressable RGB LED strip
    -   2x WS2812B RGB 144 LED Strip Light 5V White PCB Waterproof IP67)
    -   1x 5V 10A power supply to drive the LEDs

## How to setup the light

1.  Connect the WS2812b data pin (the middle wire) to GPIO 18 (or GPIO 13 for channel 2).
2.  Supply power with enough current to the WS2812b LED strip (refers to the LED's spec for exact detail).
3.  Connect the R-Pi to a network (use wired connection if on a Corp network).
4.  Power up the Raspberry Pi.
5.  Access the Jenkins server from the R-Pi to verify network connection.
6.  Clone this repository then `cd obsidian`.
7.  `sudo jenkins_status.py --check` to check the light strip.
8.  Verify the light strip show some light patterns to confirm it is connected correctly.
9.  `sudo jenkins_status.py --help` for a list of arguments to pass to this function
