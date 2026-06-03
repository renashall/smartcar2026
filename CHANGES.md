# Changes from the Original Freenove Repository

This repository began as **Freenove's** [Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi](https://github.com/Freenove/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi)
and has been adapted by **AI Code Academy** for the course *"Machine Learning with
Raspberry Pi & Smart Car."* The original Freenove project files are preserved; this
document records what has been **added, changed, or reorganized** on top of them.

_Last updated: 2026-06-03_

---

## Added

### `requirements.txt` (repo root)
Python packages used by the course, installable on Windows, macOS, Linux, or the
Raspberry Pi with `pip install -r requirements.txt`:

- `numpy`, `opencv-python`, `Pillow`, `PyQt5`
- The Raspberry Pi hardware libraries (`RPi.GPIO`, `rpi_ws281x`, `picamera`, `smbus2`)
  are listed as comments — they only install on the Pi and are handled by the setup
  scripts, so `pip` on a laptop won't choke on them.

### `setupPart1.sh` and `setupPart2.sh` (repo root)
A two-stage, mostly automated Raspberry Pi setup that replaces the manual steps. Both
scripts prompt for the Pi model and OS-image date, then reboot at the end.

- **`setupPart1.sh`** — enables SSH, VNC, and I2C; installs I2C tools, `python3-smbus`,
  and git; makes `python3` the default `python`; configures the camera interface; and
  applies the Bullseye patch.
- **`setupPart2.sh`** — updates the boot config for the camera; applies the audio
  workaround for older Pi models; installs the car libraries (`Code/build.sh` +
  `Code/setup.py`); and installs the course Python packages via `apt`
  (`python3-numpy/opencv/pil/pyqt5/picamera`) with a `pip install -r requirements.txt`
  fallback.

### `Code/User/` — new folder
Course lesson code, kept separate from the Freenove `Server` / `Client` / `Modules`
files so student work never collides with the kit's source:

- `car_setup.py` — helper that adds `Code/Server`, `Code/Client`, and `Code/Modules`
  to Python's import path. A lesson script only needs `import car_setup` at the top
  before importing car modules (e.g. `from Motor import Motor`).
- Lesson scripts: `lesson_1_components.py` … `lesson_8_multiple_face_detection.py` and
  `lesson_11_camera_gui.py`. Lesson 6 ships two files — `lesson_6_pi_camera_stream_server.py`
  (runs on the Pi) and `lesson_6_client_video_receiver.py`.
- `user.md` — notes for the folder.

### `Code/Modules/` — new folder
Shared modules the lesson scripts import (via `car_setup.py`):

- `SmartCarModules/` — the car driver modules: `Motor.py`, `Led.py`, `Buzzer.py`,
  `servo.py`, `Ultrasonic.py`, `Line_Tracking.py`, `ADC.py`, `Thread.py`, `Light.py`,
  `Command.py`, `PCA9685.py`, `audio.py`.
- `aicode101/` — machine-learning helpers: `predict.py`, `aicode101_img_utils.py`, and a
  `model/` directory.
- `utils/` — `haarcascade_frontalface_default.xml`, a MobileNet V2 TFLite feature model,
  and image-classification utilities.

### `Resources/` — new folder
Documentation PDFs organized into one place:

- `About_Battery.pdf`
- `Tutorial.pdf`

---

## Changed

### `README.md` — rewritten for the course
Added an AI Code Academy course note, full **Raspberry Pi setup** instructions for the
two `setupPart` scripts, and a **"Where to Put Your Code"** section documenting
`Code/User` and `car_setup.py`. The original Freenove Download / Support / Copyright /
About sections are kept.

### `Code/Client/Video.py` — face detection now runs on any platform
Removed the platform guard in `face_detect()`:

```python
# removed (and the now-unused `import sys`):
if sys.platform.startswith('win') or sys.platform.startswith('darwin'):
    ...
```

Previously face detection ran **only on Windows or macOS** — on Linux/Raspberry Pi the
client skipped detection and just saved the frame. With the guard gone, the same client
detects faces on **any platform, including the Raspberry Pi itself**. (The course's own
lesson scripts in `Code/User` — `lesson_7_face_tracking.py`, `lesson_8_multiple_face_detection.py`,
and `lesson_11_camera_gui.py` — were written without that restriction for the same reason.)

---

## Preserved from Freenove

The rest of the original Freenove project remains in place, including `Code/Server/`,
`Code/Client/` (apart from `Video.py` above), `Code/Patch/`, `Code/build.sh`,
`Code/setup.py`, `Datasheet/`, and `Picture/`. All original files stay under Freenove's
[Creative Commons BY-NC-SA 3.0](http://creativecommons.org/licenses/by-nc-sa/3.0/) license.
