"""Lesson 5: Line Follower.

Run this on the Raspberry Pi (the car). Put the car on a line track to test.

The car has three infrared sensors underneath: Left, Middle, and Right.
Each one reads 1 when it sees the dark line and 0 when it sees the floor.
We combine the three readings into one number and use it to decide how to drive.
"""

import car_setup          # adds the car's code folders to the import path
import time

# RPi.GPIO lets us read the Raspberry Pi's pins directly. The infrared sensors
# are wired to pins, and each pin reads either 1 (line) or 0 (floor).
import RPi.GPIO as GPIO

from Motor import Motor          # driving wheels

# ---- sensor pins (BCM numbering) ----
# These are the Raspberry Pi pin numbers each infrared sensor is plugged into.
IR_LEFT = 14
IR_MIDDLE = 15
IR_RIGHT = 23

# ---- driving speeds ----
# Each move is four wheel speeds: left-front, left-back, right-front, right-back.
# Negative on one side + positive on the other makes the car turn.
FORWARD = (800, 800, 800, 800)
SOFT_LEFT = (-1500, -1500, 2500, 2500)
HARD_LEFT = (-2000, -2000, 4000, 4000)
SOFT_RIGHT = (2500, 2500, -1500, -1500)
HARD_RIGHT = (4000, 4000, -2000, -2000)
STOP = (0, 0, 0, 0)

# ---- car parts (created in setup) ----
motor = None


def setup():
    """Create the motor and tell the Pi that the sensor pins are inputs."""
    global motor
    motor = Motor()
    GPIO.setwarnings(False)      # hide harmless "pin already in use" warnings
    GPIO.setmode(GPIO.BCM)       # use the BCM pin-numbering scheme
    # "IN" means we will READ these pins (the sensors send data TO the Pi).
    GPIO.setup(IR_LEFT, GPIO.IN)
    GPIO.setup(IR_MIDDLE, GPIO.IN)
    GPIO.setup(IR_RIGHT, GPIO.IN)


def read_sensors():
    """Return one number that describes which sensors see the line.

    Left counts as 4, Middle as 2, Right as 1. So "middle only" is 2,
    and "left and middle" is 4 + 2 = 6. This trick packs three yes/no answers
    into a single number, which makes the choices below easy to write.
    """
    left = GPIO.input(IR_LEFT)       # 1 if this sensor sees the line, else 0
    middle = GPIO.input(IR_MIDDLE)
    right = GPIO.input(IR_RIGHT)
    return left * 4 + middle * 2 + right


def choose_move(sensors):
    """Pick the right wheel speeds for the current sensor pattern."""
    # The 0b... numbers are written in binary so you can see the three sensors
    # as three digits: left, middle, right. 0b010 means "only the middle one".
    if sensors == 0b010:          # middle only -> we are centred, go straight
        return FORWARD
    if sensors == 0b100:          # left only -> drifting right, turn left a bit
        return SOFT_LEFT
    if sensors == 0b110:          # left + middle -> turn left harder
        return HARD_LEFT
    if sensors == 0b001:          # right only -> drifting left, turn right a bit
        return SOFT_RIGHT
    if sensors == 0b011:          # middle + right -> turn right harder
        return HARD_RIGHT
    return STOP                   # all three, or none -> stop (end of line / lost)


def loop():
    """Read the sensors and drive, over and over, very quickly."""
    while True:
        sensors = read_sensors()         # see where the line is
        move = choose_move(sensors)      # decide how to drive
        motor.setMotorModel(move[0], move[1], move[2], move[3])
        time.sleep(0.02)                 # a short pause keeps the steering smooth


def destroy():
    """Stop the wheels and release the pins when the program ends."""
    if motor is not None:
        motor.setMotorModel(0, 0, 0, 0)
    GPIO.cleanup()               # hand the pins back so other programs can use them


if __name__ == "__main__":
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        pass
    finally:
        destroy()
