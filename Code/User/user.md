# Code/User Folder

This folder is for AI Code Academy lesson files and your own smart car programs.

Use `Code/User` when you are writing new code for the course, testing an idea, or saving a finished lesson script. Keeping your files here prevents course work from being mixed into the original Freenove `Code/Server`, `Code/Client`, and `Code/Modules` folders.

## Using `car_setup.py`

Most lesson scripts in this folder should start with:

```python
import car_setup
```

That line lets your script import the smart car modules without writing long file paths. Put it before imports such as:

```python
from Motor import Motor
from Led import Led
from ADC import Adc
```

`car_setup.py` must stay in this folder. You only import it from your script; you do not need to edit it for normal lessons.

## Running Your Code

From the Raspberry Pi terminal:

```sh
cd smartcar2026/Code/User
python3 lesson_1_components.py
```

Replace `lesson_1_components.py` with the file you want to run.

### Run the LED lessons with `sudo`

The LED strip library (`rpi_ws281x`) needs root access on the Raspberry Pi.
Any lesson that lights the LEDs — **Lesson 1** and **Lesson 2** — must be run
with `sudo`, or it will stop with a permission error such as
`mmap() failed` / `Can't open /dev/mem`:

```sh
sudo python3 lesson_1_components.py
```

The other on-Pi lessons (motors, servo, ADC, ultrasonic, line sensors) work
without `sudo`, but running them with `sudo` is also fine.

### Where each lesson runs

- **On the Raspberry Pi (the car):** Lessons 1–5 and
  `lesson_6_pi_camera_stream_server.py`. These import the car's hardware
  modules and need the Pi's hardware libraries.
- **On the Pi *or* a laptop (Windows / macOS / Linux):**
  `lesson_6_client_video_receiver.py`, Lesson 7, Lesson 8, and Lesson 11.
  These only need `opencv-python`, `numpy`, and (for Lesson 11) `PyQt5`,
  which are listed in the repo's `requirements.txt`. When run from a laptop,
  pass the Pi's IP address on the command line (Lessons 6-client/7/8) or type
  it into the box (Lesson 11).
