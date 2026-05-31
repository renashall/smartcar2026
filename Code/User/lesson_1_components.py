"""Lesson 1: Components.

Run this on the Raspberry Pi (the car).
It shows the three main components from this lesson working together:
the front LEDs, the servo that turns the head, and the ultrasonic sensor.

Change DEMO_MODE below to try one part at a time, or leave it on "all".
"""

# car_setup must come first: it tells Python where the car's modules live.
import car_setup          # adds the car's code folders to the import path
import time               # "time" lets us pause the program with time.sleep()

# These three modules come from the car's Server folder. Each one controls a
# piece of hardware: the LED lights, the head servo, and the distance sensor.
from Led import Led
from Servo import Servo
from Ultrasonic import Ultrasonic

# ---- settings you can change ----
# Try changing this to run just one part of the demo while you learn.
DEMO_MODE = "all"         # "leds", "servo", "distance", or "all"

# The 8 LEDs are controlled with a "bitmask" - one on/off switch per LED.
# 0xFF is the number 255, which is all 8 switches turned on at once.
LED_ALL = 0xFF
LED_OFF = 0x00

# Colours are written as (red, green, blue). Each number goes from 0 to 255.
# (255, 0, 0) is full red, (0, 255, 0) is full green, and so on.
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Servo head positions, measured in degrees. 90 means "straight ahead".
HEAD_LEFT = 30
HEAD_CENTER = 90
HEAD_RIGHT = 150

# ---- car parts (created in setup) ----
# We list the parts here and set them to None for now. setup() fills them in.
# Using None first makes it clear these get created later, in one place.
led = None
servo = None
ultrasonic = None


def setup():
    """Create the hardware objects once, before the demo starts."""
    # "global" tells Python we want to change the variables defined above,
    # not make brand-new ones that only exist inside this function.
    global led, servo, ultrasonic
    led = Led()                  # get control of the LED strip
    servo = Servo()              # get control of the head servo
    ultrasonic = Ultrasonic()    # get control of the distance sensor
    servo.setServoPwm("0", HEAD_CENTER)   # face straight ahead to start


def show_leds():
    """Light all the LEDs red, then green, then blue, then turn them off."""
    print("LED demo: red, green, blue, then off")
    # Loop over our three colours and show each one for a second.
    for colour in (RED, GREEN, BLUE):
        red, green, blue = colour            # unpack the (r, g, b) tuple
        led.ledIndex(LED_ALL, red, green, blue)   # set every LED to this colour
        time.sleep(1)                        # hold the colour for 1 second
    led.ledIndex(LED_ALL, 0, 0, 0)           # 0,0,0 means "no colour" = off


def sweep_head():
    """Turn the head left, back to center, right, then center again."""
    print("Servo demo: look left, center, right")
    for angle in (HEAD_LEFT, HEAD_CENTER, HEAD_RIGHT, HEAD_CENTER):
        servo.setServoPwm("0", angle)        # channel "0" is the left/right servo
        time.sleep(0.6)                      # give the servo time to move


def read_distance():
    """Return the distance in front of the car in centimetres."""
    # The sensor sends out a sound pulse and times how long the echo takes.
    return ultrasonic.get_distance()


def loop():
    """Keep reading and printing the distance until you press Ctrl+C."""
    print("Distance demo: press Ctrl+C to stop")
    while True:                              # "while True" repeats forever
        distance = read_distance()
        print("Distance ahead:", distance, "cm")
        time.sleep(0.5)                      # wait half a second between reads


def destroy():
    """Leave the car in a safe, tidy state when the program ends."""
    # Each part might still be None if setup() failed, so check before using it.
    if led is not None:
        led.ledIndex(LED_ALL, 0, 0, 0)        # turn the LEDs off
    if servo is not None:
        servo.setServoPwm("0", HEAD_CENTER)   # center the head


# This block only runs when you start the file directly (python lesson_1...py).
# It is the "main" part of the program that ties everything together.
if __name__ == "__main__":
    try:
        setup()                              # build the hardware objects
        # Run only the part(s) chosen by DEMO_MODE above.
        if DEMO_MODE in ("leds", "all"):
            show_leds()
        if DEMO_MODE in ("servo", "all"):
            sweep_head()
        if DEMO_MODE in ("distance", "all"):
            loop()
    except KeyboardInterrupt:
        # This happens when you press Ctrl+C. We catch it so the program can
        # shut down cleanly instead of printing a scary error message.
        pass
    finally:
        # "finally" always runs, even after an error or Ctrl+C, so the car is
        # always left switched off safely.
        destroy()
