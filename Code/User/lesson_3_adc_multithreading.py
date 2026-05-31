"""Lesson 3: Multithreading and the ADC.

Run this on the Raspberry Pi (the car).
The ADC (analog-to-digital converter) lets us read sensors that give a voltage:
the two light sensors (photoresistors) and the battery.

The main loop keeps printing the light readings, while a SECOND thread quietly
watches the battery in the background and beeps the buzzer if it gets low.
That is what "multithreading" means: two things happening at the same time.
"""

import car_setup          # adds the car's code folders to the import path
import time

# A "thread" is a separate line of work that runs at the same time as the rest
# of your program. "Event" is a simple on/off flag we use to tell the thread
# when it is time to stop.
from threading import Thread, Event

from ADC import Adc           # reads sensor voltages
from Buzzer import Buzzer     # the beeper, used for the low-battery warning

# ---- ADC channels ----
# The ADC has several inputs ("channels"), numbered 0, 1, 2... Each sensor is
# wired to one channel, so we read a sensor by reading its channel number.
LEFT_LIGHT = 0
RIGHT_LIGHT = 1
BATTERY = 2               # this reading times 3 gives the battery pack voltage

# ---- battery settings ----
# The battery is healthy around 8 volts and needs charging as it drops.
LOW_BATTERY = 7.0         # volts: beep twice as a warning
CRITICAL_BATTERY = 6.8    # volts: beep four times, time to charge

# ---- car parts (created in setup) ----
adc = None
buzzer = None
stop_event = Event()      # starts "not set"; we set() it to stop the thread
battery_thread = None


def setup():
    """Create the sensors and start the background battery-watching thread."""
    global adc, buzzer, battery_thread
    adc = Adc()
    buzzer = Buzzer()

    # Build the second thread. target=monitor_battery means "run that function".
    battery_thread = Thread(target=monitor_battery)
    # A "daemon" thread is allowed to stop automatically when the main program
    # ends, so it never holds the program open by itself.
    battery_thread.daemon = True
    battery_thread.start()    # actually begin running monitor_battery() now


def read_battery_voltage():
    """Read the battery channel and scale it up to the real pack voltage."""
    # The ADC only sees one third of the battery voltage, so we multiply by 3.
    return adc.recvADC(BATTERY) * 3


def battery_percent(voltage):
    """Turn a voltage into a rough 0-100% charge estimate."""
    # Around 7.0 V is "empty" and about 8.4 V is "full", so we map that range
    # onto 0-100. int(...) drops the decimals to give a whole number.
    return int((voltage - 7) / 1.40 * 100)


def beep(times):
    """Beep the buzzer on and off a chosen number of times."""
    for _ in range(times):       # "_" is a throwaway name: we just want to repeat
        buzzer.run("1")          # buzzer on
        time.sleep(0.1)
        buzzer.run("0")          # buzzer off
        time.sleep(0.1)


def monitor_battery():
    """Runs in the background thread, checking the battery every few seconds."""
    # Keep looping until someone calls stop_event.set() (see destroy()).
    while not stop_event.is_set():
        voltage = read_battery_voltage()
        print("Battery:", round(voltage, 2), "V (", battery_percent(voltage), "% )")
        # Warn louder the lower the battery gets.
        if voltage <= CRITICAL_BATTERY:
            beep(4)
        elif voltage <= LOW_BATTERY:
            beep(2)
        time.sleep(3)            # wait 3 seconds before checking again


def loop():
    """The MAIN thread: keep printing the two light-sensor readings."""
    while True:
        left = adc.recvADC(LEFT_LIGHT)    # voltage from the left light sensor
        right = adc.recvADC(RIGHT_LIGHT)  # voltage from the right light sensor
        # round(value, 2) keeps just two decimal places so it is easy to read.
        print("Light  left:", round(left, 2), "V   right:", round(right, 2), "V")
        time.sleep(1)


def destroy():
    """Stop the background thread and close the sensors cleanly."""
    stop_event.set()             # flip the flag so monitor_battery() can finish
    if battery_thread is not None:
        # join() waits for the thread to actually finish. timeout=2 means
        # "wait at most 2 seconds" so we never hang forever.
        battery_thread.join(timeout=2)
    if buzzer is not None:
        buzzer.run("0")          # make sure the buzzer is off
    if adc is not None:
        adc.i2cClose()           # close the connection to the ADC chip


if __name__ == "__main__":
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        pass
    finally:
        destroy()
