#!/usr/bin/env python3
# Reused colorWipe from NeoPixel library strandtest example

import time
from neopixel import *
import argparse

from requests import get

# LED strip configuration:
LED_COUNT = 144  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10  # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 55  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53


def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)


def progress_bar(strip, percentage, progressColor=Color(0, 255, 0), remainColor=Color(255, 0, 0), wait_ms=50):
    finishedProgress = int(strip.numPixels() * (percentage / 100.0))
    print("Finished Progress: {0}".format(finishedProgress))
    for index in range(0, finishedProgress):
        strip.setPixelColor(index, progressColor)

    for index in range(finishedProgress, strip.numPixels()):
        strip.setPixelColor(index, remainColor)

    strip.show()
    return finishedProgress


def blink_and_wait(strip, pixel, progressColor=Color(0, 255, 0), remainColor=Color(255, 0, 0), wait_ms=250, repeat=10):
    for index in range(0, repeat):
        strip.setPixelColor(pixel, remainColor)
        strip.show()
        time.sleep(wait_ms / 1000.0)
        strip.setPixelColor(pixel, Color(0, 0, 0))
        strip.show()
        time.sleep(wait_ms / 1000.0)
        strip.setPixelColor(pixel, progressColor)
        strip.show()
        time.sleep(wait_ms / 1000.0)


if __name__ == '__main__':
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    parser.add_argument('-s', '--server', action='store', help='Jenkins Server')
    parser.add_argument('-j', '--job', action='store', help='Job name')
    args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    print('Press Ctrl-C to quit.')
    if not args.clear:
        print('Use "-c" argument to clear LEDs on exit')

    job_url = args.server + "/job/" + args.job + "/lastBuild/api/json"
    progress_url = args.server + "/job/" + args.job + "/lastBuild/api/json?tree=executor[progress]"

    print("=" * 20)
    print("Monitoring job URL: %s" % job_url)
    print("With Progress URL: %s" % progress_url)
    print("=" * 20)
    pixel = 0
    try:
        while (True):
            response = get(job_url, verify=False)
            print(response)
            job_detail = response.json()
            if job_detail["result"]:
                print("Done")
                colorWipe(strip, Color(0, 0, 0), 10)
                time.sleep(10)
            else:
                response = get(progress_url)
                progress = int(response.json()["executor"]["progress"])
                pixel = progress_bar(strip, progress, Color(255, 0, 0), Color(100, 255, 0))
                blink_and_wait(strip, pixel)
    except KeyboardInterrupt:
        if args.clear:
            colorWipe(strip, Color(0, 0, 0), 10)
