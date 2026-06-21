"""Lesson 4: Autonomous Modes.

Run this on the Raspberry Pi (the car). Test on the floor with space to move!

This script has two self-driving modes. Pick one with DEMO_MODE:
  "light"  - M-Light: the car drives toward the brightest light using the two
             light sensors.
  "sonic"  - M-Sonic: the car looks left, ahead, and right with the ultrasonic
             sensor and steers around obstacles.
"""

import car_setup          # adds the car's code folders to the import path
import time

from motor import Motor          # driving wheels
from adc import Adc              # reads the light sensors (for "light" mode)
from servo import Servo          # turns the head (module file is "servo.py", lowercase)
from ultrasonic import Ultrasonic   # measures distance (for "sonic" mode)

# ---- settings you can change ----
DEMO_MODE = "sonic"       # "light" or "sonic"
DRIVE_SPEED = 1200        # forward power (0 = stop, up to 4095 = full)
TURN_SPEED = 1500         # turning power

# M-Light settings: the light sensors live on ADC channels 0 and 1.
# A LOWER voltage means MORE light is hitting that sensor.
LEFT_LIGHT = 0
RIGHT_LIGHT = 1
BRIGHT_ENOUGH = 2.99      # below this, both sides see light, so go forward
SIDE_DIFFERENCE = 0.15    # if one side is this much brighter, turn toward it

# M-Sonic settings: head angles to check, and what counts as "too close".
HEAD_LEFT = 30
HEAD_CENTER = 90
HEAD_RIGHT = 150
BLOCKED = 30              # closer than this (in cm) counts as an obstacle

# ---- car parts (created in setup) ----
# We only create the parts the chosen mode actually needs, so some of these
# may stay None.
motor = None
adc = None
servo = None
ultrasonic = None


def setup():
    """Create just the hardware the chosen DEMO_MODE needs."""
    global motor, adc, servo, ultrasonic
    motor = Motor()                      # both modes need to drive
    if DEMO_MODE == "light":
        adc = Adc()                      # light mode needs the light sensors
    else:
        servo = Servo()                  # sonic mode needs the head + sensor
        ultrasonic = Ultrasonic()
        servo.setServoPwm("0", HEAD_CENTER)   # start looking straight ahead


def light_step():
    """One step of light-following: read both sensors and steer toward light."""
    left = adc.recvADC(LEFT_LIGHT)
    right = adc.recvADC(RIGHT_LIGHT)
    # Remember: smaller voltage = brighter.
    if left < BRIGHT_ENOUGH and right < BRIGHT_ENOUGH:
        # Both sides see plenty of light, so drive straight ahead.
        motor.setMotorModel(DRIVE_SPEED, DRIVE_SPEED, DRIVE_SPEED, DRIVE_SPEED)
    elif left - right > SIDE_DIFFERENCE:
        # The right sensor is brighter (its voltage is lower), so turn right.
        motor.setMotorModel(-TURN_SPEED, -TURN_SPEED, TURN_SPEED, TURN_SPEED)
    elif right - left > SIDE_DIFFERENCE:
        # The left sensor is brighter, so turn left.
        motor.setMotorModel(TURN_SPEED, TURN_SPEED, -TURN_SPEED, -TURN_SPEED)
    else:
        # Light is roughly even and dim: stop and wait.
        motor.setMotorModel(0, 0, 0, 0)


def look(angle):
    """Turn the head to an angle and measure the distance there (in cm)."""
    servo.setServoPwm("0", angle)
    time.sleep(0.3)                      # give the head time to finish moving
    return ultrasonic.get_distance()


def sonic_step():
    """One step of obstacle-avoiding: look ahead, and turn if something blocks us."""
    ahead = look(HEAD_CENTER)
    if ahead > BLOCKED:
        # The path ahead is clear, so drive forward.
        motor.setMotorModel(DRIVE_SPEED, DRIVE_SPEED, DRIVE_SPEED, DRIVE_SPEED)
        return

    # Something is in front: stop, then look left and right to choose a way.
    motor.setMotorModel(0, 0, 0, 0)
    left = look(HEAD_LEFT)
    right = look(HEAD_RIGHT)
    servo.setServoPwm("0", HEAD_CENTER)  # put the head back to the middle
    # Turn toward whichever side has more room.
    if left > right:
        motor.setMotorModel(-TURN_SPEED, -TURN_SPEED, TURN_SPEED, TURN_SPEED)
    else:
        motor.setMotorModel(TURN_SPEED, TURN_SPEED, -TURN_SPEED, -TURN_SPEED)
    time.sleep(0.5)                      # turn for half a second before re-checking


def loop():
    """Repeat the chosen mode's single step over and over."""
    while True:
        if DEMO_MODE == "light":
            light_step()
        else:
            sonic_step()
        time.sleep(0.05)                 # a tiny pause so the loop is not too frantic


def destroy():
    """Stop the car and tidy up the hardware we used."""
    if motor is not None:
        motor.setMotorModel(0, 0, 0, 0)       # stop driving
    if servo is not None:
        servo.setServoPwm("0", HEAD_CENTER)   # face the head forward again
    if adc is not None:
        adc.i2cClose()                        # close the sensor connection


if __name__ == "__main__":
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        pass
    finally:
        destroy()
