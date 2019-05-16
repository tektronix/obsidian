#!/usr/bin/env python3
# Display a Jenkins build job status and progress

# Re-use animation functions from https://github.com/jgarff/rpi_ws281x/blob/master/python/examples/strandtest.py

import argparse
import random
import sys
import time

from neopixel import *
from requests import get

MAX_LED_COUNT = 10000
POLL_PERIOD_SECONDS = 10

# LED strip default configuration:
LED_COUNT = 144  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10  # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 55  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

JENKINS_FAILURE = 'FAILURE'
JENKINS_SUCCESS = 'SUCCESS'
JENKINS_ABORTED = 'ABORTED'
JENKINS_NO_RESULT = None

COLOR_RED = Color(0, 255, 0)
COLOR_GREEN = Color(255, 0, 0)
COLOR_BLUE = Color(0, 0, 255)
COLOR_WHITE = Color(255, 255, 255)
COLOR_BLACK = Color(0, 0, 0)


def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)


def theaterChase(strip, color, wait_ms=50, iterations=10):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, color)
            strip.show()
            time.sleep(wait_ms / 1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, 0)


def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)


def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256 * iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)


def rainbowCycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256 * iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)


def theaterChaseRainbow(strip, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, wheel((i + j) % 255))
            strip.show()
            time.sleep(wait_ms / 1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, 0)


def colorShuffle(strip, color, wait_ms=50):
    """Shuffle color onto display a pixel at a time."""
    indexes = [i for i in range(strip.numPixels())]
    random.shuffle(indexes)
    for i in indexes:
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)


def tail_entry(strip, pixel, color, bg_color=COLOR_BLACK, travel_time_ms=100):
    """Animate a pixel enter from the tail of the strip to the specified pixel"""
    if strip.numPixels() > pixel:
        wait_ms = travel_time_ms / float((strip.numPixels() - pixel))
    else:
        wait_ms = travel_time_ms

    for j in range(strip.numPixels(), pixel - 1, -1):
        strip.setPixelColor(j, color)
        for k in range(j + 1, strip.numPixels()):
            strip.setPixelColor(k, bg_color)
        strip.show()
        time.sleep(wait_ms / 1000.0)


def head_entry(strip, pixel, color, bg_color=COLOR_BLACK, travel_time_ms=1000):
    """Animate a pixel enter from the head of the strip to the specified pixel"""
    wait_ms = travel_time_ms / pixel
    for j in range(pixel):
        strip.setPixelColor(j, color)
        for i in range(j):
            strip.setPixelColor(i, bg_color)
        strip.show()
        time.sleep(wait_ms / 1000.0)


def solid(strip, color):
    head_solid(strip, strip.numPixels(), color=color)


def head_solid(strip, pixel, color):
    """Set solid color from the head of the strip to the specified pixel"""
    for i in range(pixel):
        strip.setPixelColor(i, color)
    strip.show()


def tail_solid(strip, pixel, color):
    """Set solid color from the specified pixel to the end of the strip"""
    for i in range(strip.numPixels, pixel - 1):
        strip.setPixelColor(i, color)
    strip.show()


def tail_fill(strip, color, bg_color=COLOR_BLACK, travel_time_ms=100):
    """Tail fill the entire strip"""
    for i in range(strip.numPixels()):
        tail_entry(strip, i, color=color, bg_color=bg_color, travel_time_ms=travel_time_ms)
        head_solid(strip, i, color=color)


def progress_bar_tail_entry(strip, pixel, color, bg_color=COLOR_BLACK, travel_time_ms=100):
    """Animate the last fill from tail end up to the specified pixel"""
    head_solid(strip, pixel, color=color)
    tail_entry(strip, pixel, color=color, bg_color=bg_color, travel_time_ms=travel_time_ms)


def progress_bar_tail_fill(strip, pixel, color, bg_color=COLOR_BLACK, travel_time_ms=100):
    """Animate progress bar fill from tail end from start up to the specified pixel"""
    for i in range(pixel):
        head_solid(strip, i, color=color)
        tail_entry(strip, i, color=color, bg_color=bg_color, travel_time_ms=travel_time_ms)


def progress_bar(strip, percentage, progressColor, remainColor=COLOR_BLACK, wait_ms=10):
    """Animate progress bar"""
    finishedProgress = strip.numPixels() * percentage / 100
    for index in range(0, finishedProgress):
        strip.setPixelColor(index, progressColor)

    for index in range(finishedProgress, strip.numPixels()):
        strip.setPixelColor(index, remainColor)
        strip.show()
    rainbowPixel(strip, finishedProgress, wait_ms=wait_ms)


def rainbowPixel(strip, pixel, wait_ms=10):
    """Cycle all colors for a given pixel"""
    for j in range(256):
        strip.setPixelColor(pixel, wheel(j))
        strip.show()
        time.sleep(wait_ms / 1000.0)


def show_success(strip):
    """Animate build result success"""
    colorWipe(strip, COLOR_GREEN, 10)


def show_failure(strip):
    """Animate build result failure"""
    colorWipe(strip, COLOR_RED, 10)


def show_aborted(strip):
    """Animate build result aborted"""
    colorWipe(strip, Color(200, 200, 200), 10)


def show_build_started(strip):
    """Animate build started"""
    colorShuffle(strip, color=COLOR_BLACK, wait_ms=10)


def show_build_in_progress(strip, progress, travel_time_s=POLL_PERIOD_SECONDS):
    """
    Animate build in progress
    """
    pixel = progress * strip.numPixels() / 100
    print("progress=%s%% => pixel=%s" % (progress, pixel))
    if pixel == strip.numPixels():
        travel_time_ms = 1000
    else:
        travel_time_ms = travel_time_s * 1000
    progress_bar_tail_entry(strip, pixel, color=COLOR_BLUE, travel_time_ms=travel_time_ms)


def show_build_finished(strip):
    """Animate build is finished"""
    theaterChase(strip, Color(153, 0, 153), iterations=20)


def light_check(strip):
    """Check each RGB pixel"""
    travel_time = 100

    solid(strip, color=COLOR_BLACK)

    head_entry(strip, strip.numPixels(), color=COLOR_RED, travel_time_ms=travel_time)
    tail_entry(strip, 0, color=COLOR_RED, travel_time_ms=travel_time)
    head_entry(strip, strip.numPixels(), color=COLOR_GREEN, travel_time_ms=travel_time)
    tail_entry(strip, 0, color=COLOR_GREEN, travel_time_ms=travel_time)
    head_entry(strip, strip.numPixels(), color=COLOR_BLUE, travel_time_ms=travel_time)
    tail_entry(strip, 0, color=COLOR_BLUE, travel_time_ms=travel_time)
    head_entry(strip, strip.numPixels(), color=COLOR_WHITE, travel_time_ms=travel_time)
    tail_entry(strip, 0, color=COLOR_WHITE, travel_time_ms=travel_time)

    solid(strip, color=COLOR_RED)
    time.sleep(1)
    solid(strip, color=COLOR_GREEN)
    time.sleep(1)
    solid(strip, color=COLOR_BLUE)
    time.sleep(1)
    solid(strip, color=COLOR_WHITE)
    time.sleep(1)

    solid(strip, color=COLOR_BLACK)


def validate_brightness_value(value):
    """Validate the brightness value"""
    error_message = "The value of brightness must be between %d and %d."
    return validate_range(value, 0, 255, error_message)


def validate_gpio_pin(value):
    """Validate the GPIO pin number"""
    error_message = "GPIO on a Raspberry Pi should be between %d and %d."
    return validate_range(value, 1, 27, error_message)


def validate_range(value, min_value, max_value, error_message):
    """Validate a value is between a given range (inclusive)"""
    x = int(value)
    if min_value <= x <= max_value:
        return x
    raise argparse.ArgumentTypeError(error_message % (min_value, max_value))


def validate_led_count(value):
    """Validate the LED Count"""
    error_message = "The number of LED on a single strip should be between %d and %d"
    return validate_range(value, 1, MAX_LED_COUNT, error_message)


def validate_poll_period(value):
    """Validate the period to poll for status"""
    seconds_per_day = 60 * 60 * 24
    error_message = "The period to poll for status change should be between between %d and %d"
    return validate_range(value, 1, seconds_per_day, error_message)


def process_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--check', action='store_true', help='Run a few light patterns to check the LED pixels.')
    parser.add_argument('-b', '--brightness', action='store', type=validate_brightness_value,
                        help='The brightness level of the LEDs, where 0 is darkest and 255 is brightest',
                        default=LED_BRIGHTNESS)
    parser.add_argument('-d', '--donotclear', action='store_true',
                        help='Leave the display as is without clearing it on exit')
    parser.add_argument('-s', '--server', action='store',
                        help='a URL to a Jenkins Server.  Example:  http://somejenkins.com:8080')
    parser.add_argument('-j', '--job', action='store', help='Job name')
    parser.add_argument('-p', '--pin', action='store', type=validate_gpio_pin,
                        help='The GPIO pin to use to drive the LED', default=LED_PIN)
    parser.add_argument('-l', '--length', action='store', type=validate_led_count,
                        help='The number of LED in the LED strip', default=LED_COUNT)
    parser.add_argument('-p', '--pollperiod', action='store', type=validate_poll_period,
                        help='The number of seconds to wait between polling for status.', default=POLL_PERIOD_SECONDS)

    return parser.parse_args()


if __name__ == '__main__':
    args = process_args()

    if args.length <= 0:
        print("Not enough LED to work with!")
        sys.exit()

    strip = Adafruit_NeoPixel(args.length, args.pin, LED_FREQ_HZ, LED_DMA, LED_INVERT, args.brightness, LED_CHANNEL)
    strip.begin()

    if args.check:
        light_check(strip)
        sys.exit()

    if not args.server or not args.job:
        print("A Jenkins Server and a Job name are required to query for status.  "
              "Run this command again with the -h or --help on how to specify them.")
        sys.exit()

    job_url = args.server + "/job/" + args.job + "/lastBuild/api/json"
    progress_url = args.server + "/job/" + args.job + "/lastBuild/api/json?tree=executor[progress]"
    print('Monitor job: %s' % job_url)
    print("")
    print('Press Ctrl-C to quit.')

    is_building = True

    try:
        while (True):
            response = get(job_url, verify=False)
            job_status = response.json()
            if job_status["result"] == JENKINS_NO_RESULT:
                if not is_building:
                    show_build_started(strip)
                is_building = True
                response = get(progress_url)
                progress = int(response.json()["executor"]["progress"])
                show_build_in_progress(strip, progress, travel_time_s=args.pollperiod)
            else:
                if is_building:
                    show_build_in_progress(strip, 100, travel_time_s=1)
                    show_build_finished(strip)
                    print("Done with status: %s" % job_status["result"])
                    if job_status["result"] == JENKINS_FAILURE:
                        show_failure(strip)
                    elif job_status["result"] == JENKINS_SUCCESS:
                        show_success(strip)
                    elif job_status["result"] == JENKINS_ABORTED:
                        show_aborted(strip)
                is_building = False
                time.sleep(5)
    except KeyboardInterrupt:
        print("\nKeyboard Interrupt signal received.")
        if not args.donotclear:
            print("Clearing all LEDs...")
            colorWipe(strip, COLOR_BLACK, wait_ms=5)
