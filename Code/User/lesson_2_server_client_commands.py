"""Lesson 2: Server and Client.

Run this on the Raspberry Pi (the car).
The client and server talk to each other using short text commands that look
like  CMD_MOTOR#1500#1500#1500#1500 .  This script shows two things:

1) how to build one of those command strings (format_command), and
2) how the car actually carries out those commands by driving the motors,
   sounding the buzzer, and lighting the LEDs.

The full Freenove programs use the same idea:

- Code/Server/main.py runs on the Raspberry Pi car. It opens the command server
  on port 5000, opens the video server on port 8000, reads hardware sensors,
  and carries out commands like CMD_MOTOR, CMD_BUZZER, and CMD_LED.
- Code/Client/main.py is the graphical controller. It connects to the server,
  sends those text commands when you press buttons, and shows the camera video
  and live sensor/battery information.

This lesson does not start those full windows. Instead, it slows the idea down:
we print the command string first, then call the same kind of hardware action
directly so you can see how the message maps to the car's behavior.
"""

import car_setup          # adds the car's code folders to the import path
import time

# Bring in the parts we control in this lesson.
from motor import Motor       # the four driving wheels
from buzzer import Buzzer     # the beeper
from led import Led           # the LED lights
from command import COMMAND   # the list of command names the car understands

# ---- settings you can change ----
# Motor power goes from 0 (stopped) up to 4095 (full speed). 1500 is gentle.
DRIVE_SPEED = 1500

# A "move" is four motor values, one for each wheel, in this order:
#   left-front, left-back, right-front, right-back.
# A positive number spins the wheel forward; a negative number spins it back.
# To turn, we spin the wheels on one side backward and the other side forward.
FORWARD = (DRIVE_SPEED, DRIVE_SPEED, DRIVE_SPEED, DRIVE_SPEED)
BACKWARD = (-DRIVE_SPEED, -DRIVE_SPEED, -DRIVE_SPEED, -DRIVE_SPEED)
TURN_LEFT = (-DRIVE_SPEED, -DRIVE_SPEED, DRIVE_SPEED, DRIVE_SPEED)
TURN_RIGHT = (DRIVE_SPEED, DRIVE_SPEED, -DRIVE_SPEED, -DRIVE_SPEED)
STOP = (0, 0, 0, 0)

# 0xFF is 255, which means "all eight LEDs at once".
LED_ALL = 0xFF

# ---- car parts (created in setup) ----
motor = None
buzzer = None
led = None
cmd = None


def setup():
    """Create the hardware objects and the command-name helper."""
    global motor, buzzer, led, cmd
    motor = Motor()
    buzzer = Buzzer()
    led = Led()
    cmd = COMMAND()       # COMMAND holds the command names like cmd.CMD_MOTOR


def format_command(name, values):
    """Build a command string like the client sends, e.g. CMD_MOTOR#1500#1500.

    The car's client and server glue the command name and its values together
    with "#" between them. This function does the same so you can SEE the
    message that would travel across the network.
    """
    parts = [name]                  # start the list with the command name
    for value in values:            # add each value, turned into text
        parts.append(str(value))
    return "#".join(parts)          # join everything with "#" between the parts


def drive(move, seconds):
    """Run one move for a number of seconds, printing the matching command."""
    print("Sending:", format_command(cmd.CMD_MOTOR, move))
    # setMotorModel takes the four wheel speeds and drives the motors.
    motor.setMotorModel(move[0], move[1], move[2], move[3])
    time.sleep(seconds)             # keep driving for this many seconds


def test_buzzer():
    """Beep the buzzer on, then off."""
    print("Sending:", format_command(cmd.CMD_BUZZER, ["1"]))
    buzzer.run("1")       # the buzzer uses the text "1" for on and "0" for off
    time.sleep(1)
    buzzer.run("0")


def test_leds():
    """Turn every LED blue for a moment, then off."""
    print("Sending:", format_command(cmd.CMD_LED, [LED_ALL, 0, 0, 255]))
    led.ledIndex(LED_ALL, 0, 0, 255)   # 0 red, 0 green, 255 blue = blue
    time.sleep(1)
    led.ledIndex(LED_ALL, 0, 0, 0)     # all zeros = off


def loop():
    """Run through the whole demo once: drive, beep, then flash the LEDs."""
    drive(FORWARD, 1)
    drive(BACKWARD, 1)
    drive(TURN_LEFT, 1)
    drive(TURN_RIGHT, 1)
    drive(STOP, 1)        # stop the wheels before the next tests
    test_buzzer()
    test_leds()


def destroy():
    """Make sure the car is fully stopped and quiet when we finish."""
    if motor is not None:
        motor.setMotorModel(0, 0, 0, 0)   # stop all wheels
    if buzzer is not None:
        buzzer.run("0")                   # silence the buzzer
    if led is not None:
        led.ledIndex(LED_ALL, 0, 0, 0)    # turn the LEDs off


if __name__ == "__main__":
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        pass                              # Ctrl+C: stop quietly
    finally:
        destroy()                         # always leave the car safe
