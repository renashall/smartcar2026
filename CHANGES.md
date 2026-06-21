# Changes from the Original Freenove Repository

This repository began as **Freenove's** [Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi](https://github.com/Freenove/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi)
and has been adapted by **AI Code Academy** for the course *"Machine Learning with
Raspberry Pi & Smart Car."* The original Freenove project files are preserved; this
document records what has been **added, changed, or reorganized** on top of them.

_Last updated: 2026-06-21_

---

## Added

### `requirements.txt` (repo root)
Python packages used by the course, installable on Windows, macOS, Linux, or the
Raspberry Pi with `pip install -r requirements.txt`:

- `numpy`, `opencv-python`, `Pillow`, `PyQt5`
- The Raspberry Pi hardware libraries (`RPi.GPIO`, `rpi_ws281x`, `picamera`, `smbus2`)
  are listed as comments — they only install on the Pi and are handled by the setup
  scripts, so `pip` on a laptop won't choke on them.

### `Code/setup.py` — cross-platform laptop/desktop installer
A single Python script that replaces the old per-OS `Code/setup_macos.py` and
`Code/setup_windows.py`. Run it from the repo root with the system Python (`python Code/setup.py` on Windows,
`python3 Code/setup.py` on macOS/Linux) and it:

- detects the operating system (Windows / macOS / Linux);
- creates a `.venv` virtual environment in the repo root (reused if present, or
  rebuilt with `--force`); and
- installs the packages from `requirements.txt` into that `.venv`.

It needs no administrator/`sudo` (it only writes a project-local `.venv`), prints the
OS-specific activation command when it finishes, and prints manual fallback commands if
a step fails. It detects a Raspberry Pi and points the user at the setup scripts instead
(a `.venv` would hide the Pi's apt-installed system packages); `--pi` overrides this.

### `Code/setupPart1.sh` and `Code/setupPart2.sh`
A two-stage, automated Raspberry Pi setup that replaces the manual steps. Both scripts
auto-detect the Pi model, OS, and camera stack, then reboot at the end.

- **`setupPart1.sh`** — enables SSH, VNC, and I2C; installs I2C tools, `python3-smbus`,
  and git; makes `python3` the default `python`; configures the camera interface; and
  applies the Bullseye patch (only where the legacy camera stack needs it).
- **`setupPart2.sh`** — updates the boot config for the camera; applies the audio
  workaround for older Pi models; installs the addressable-LED (WS281x) driver; and
  installs the course Python packages via `apt`
  (`python3-numpy/opencv/pil/pyqt5/picamera2`).

### `Code/User/` — new folder
Course lesson code, kept separate from the Freenove `Server` / `Client` / `Modules`
files so student work never collides with the kit's source:

- `car_setup.py` — helper that adds `Code/Server` and `Code/Client` to Python's
  import path. A lesson script only needs `import car_setup` at the top before
  importing car modules (e.g. `from motor import Motor`).
- Lesson scripts: `lesson_1_components.py` … `lesson_8_multiple_face_detection.py` and
  `lesson_11_camera_gui.py`. Lesson 6 ships two files — `lesson_6_pi_camera_stream_server.py`
  (runs on the Pi) and `lesson_6_client_video_receiver.py`.
- `user.md` — notes for the folder.

### `Resources/` — new folder
Documentation PDFs organized into one place:

- `About_Battery.pdf`
- `Tutorial.pdf`

---

## Changed

### `README.md` — rewritten for the course
Added an AI Code Academy course note, a **Computer (laptop/desktop) Setup** section for
`Code/setup.py`, full **Raspberry Pi setup** instructions for the two `Code/setupPart`
scripts, and a **"Where to Put Your Code"** section documenting `Code/User` and
`car_setup.py`. The original Freenove Download / Support / Copyright / About sections are
kept.

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

### `Code/Client/video.py` — video frames are written atomically
`face_detect()` now renders each frame to `video_tmp.jpg` and `os.replace()`s it onto
`video.jpg` in a single step, instead of writing `video.jpg` in place. `cv2.imwrite` is
not atomic, so the streaming thread could be caught mid-write by the GUI's display timer;
the partial JPEG failed validation and the client flashed the "No video available"
placeholder between good frames. The atomic rename guarantees the reader always sees a
complete frame, removing the flicker.

### `Code/Server/servo.py` — servo commands are clamped to safe hardware ranges
Servo angles are now clamped to `0..180` degrees, and converted PWM pulses are clamped
to the standard `500..2500 us` range before being sent to the PCA9685. This keeps the
horizontal ultrasonic servo from receiving out-of-range pulses at the far right end of
the client control.

---

## Removed / moved

- **`Code/setup_macos.py` and `Code/setup_windows.py`** — the two per-OS pip installers
  were replaced by the single cross-platform `Code/setup.py` (see *Added*).
- **`Code/build.sh` and the original Freenove Pi-oriented `Code/setup.py` helper** — removed.
  The only car-specific step they performed (installing the WS281x LED driver) is now
  done inline by `setupPart2.sh`; making `python3` the default and installing
  `python3-pyqt5` were already handled by the `setupPart` scripts.
- **`setupPart1.sh` / `setupPart2.sh`** — moved from the repo root into `Code/` and
  updated to locate the project by `Code/Server/main.py` instead of the removed
  `build.sh` / the original Freenove Pi setup helper.

---

## Preserved from Freenove

The rest of the original Freenove project remains in place, including `Code/Server/`,
`Code/Client/` (apart from `Video.py` above), `Code/Patch/`, `Datasheet/`, and
`Picture/`. All original files stay under Freenove's
[Creative Commons BY-NC-SA 3.0](http://creativecommons.org/licenses/by-nc-sa/3.0/) license.
