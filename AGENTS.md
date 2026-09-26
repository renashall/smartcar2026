# Agent Guide — Smart-Car-Level-3

Shared guidance for LLM agents (Claude, Codex, Gemini, etc.) working in this
repository. `CLAUDE.md` is a symlink to this file.

## What this repo is

A fork of Freenove's **4WD Smart Car Kit for Raspberry Pi**, adapted by
AI Code Academy for the course *"Machine Learning with Raspberry Pi & Smart Car."*
The original Freenove files are preserved; course material is added on top.
See `CHANGES.md` for the full list of additions.

## Layout

- `Code/Server/` — Freenove car driver modules + the TCP server (`main.py`,
  `server.py`). Runs on the Raspberry Pi. **Preserved Freenove code** — avoid
  editing unless necessary.
- `Code/Client/` — Freenove desktop client (PyQt5). Preserved Freenove code.
- `Code/User/` — **course lesson scripts** (the primary place for new work).
  Keep student/course code here, separate from the Freenove source. This folder
  holds the lesson `.py` files alongside the shared `car_setup.py` helper and
  `USER.md` notes.
- `Application/`, `Code/Patch/`, `Datasheet/`, `Resources/` — original app
  files, assets, datasheets, and patches.
- `Code/setupPart1.sh` / `Code/setupPart2.sh` — two-stage Raspberry Pi setup
  (they locate the repo via `Code/Server/main.py`).
- `Code/setup.py` — cross-platform laptop/desktop installer: detects the
  OS, creates `.venv` in the repo root, and installs root `requirements.txt` into it.
  Not for the Pi (it detects a Pi and defers to the `setupPart` scripts).
- `requirements.txt` — laptop-installable Python deps (Pi-only libs are
  commented out so `pip` on a laptop won't choke).

## How `Code/User` lessons work

- Each on-Pi lesson starts with `import car_setup` BEFORE importing any car
  module. `car_setup.py` adds `Code/Server` and `Code/Client` to `sys.path`, so
  imports like `from Motor import Motor` resolve to the Server modules.
  `car_setup.CODE_DIR` points at `Code/`.
- **Module name casing matters.** The Raspberry Pi filesystem is
  case-sensitive. Import names must match the real filenames exactly, e.g.
  `from servo import Servo` (the file is `servo.py`, lowercase) — `from Servo`
  fails on the Pi even though it works on Windows/macOS. Other files are
  capitalized: `Motor.py`, `Led.py`, `Buzzer.py`, `ADC.py`, `Ultrasonic.py`,
  `Command.py`.
- Module → class/method quick reference used by the lessons:
  - `from Motor import Motor` → `Motor().setMotorModel(lf, lb, rf, rb)` (-4095..4095)
  - `from servo import Servo` → `Servo().setServoPwm("0".."7", angle)` (channel is a string)
  - `from Led import Led` → `Led().ledIndex(bitmask, R, G, B)`
  - `from Buzzer import Buzzer` → `Buzzer().run("1" | "0")`
  - `from ADC import Adc` → `Adc().recvADC(channel)` (volts), `.i2cClose()`
  - `from Ultrasonic import Ultrasonic` → `Ultrasonic().get_distance()` (cm)
  - `from Command import COMMAND` → command-name constants (`CMD_MOTOR`, `CMD_SERVO`, …)

## Running lessons

- **On the Pi:** Lessons 1–5 and `lesson_6_pi_camera_stream_server.py`.
  Run LED lessons (1, 2) with **`sudo`** — `rpi_ws281x` needs root
  (`Can't open /dev/mem` otherwise). On a Pi 5, `led.py`
  uses the `Adafruit-Blinka-Raspberry-Pi5-Neopixel` driver instead of `rpi_ws281x`.
- **On the Pi or a laptop:** `lesson_6_client_video_receiver.py`, Lessons 7, 8,
  11. Need `opencv-python`, `numpy`, and (Lesson 11) `PyQt5`. Pass the Pi's IP
  on the command line, or type it into Lesson 11's box.
- Lessons 7/8/11 talk to the Freenove server (`main.py`) on ports 8000 (video)
  and 5000 (commands). The video protocol is `[4-byte little-endian length]
  [JPEG bytes]`, terminated by a length of 0.

## Conventions for agents

- Treat `Code/Server` and `Code/Client` as upstream Freenove code; prefer adding
  new work under `Code/User`. Record any deviation in `CHANGES.md`.
- Python: use a virtualenv (`.venv` here, gitignored). Never install globally.
- When verifying, the laptop-side lessons (6-client/7/8/11) can be import-tested
  off-Pi after `pip install numpy opencv-python PyQt5`. The hardware lessons can
  only be `py_compile`-checked off-Pi.
- Keep scratch output in `.tmp/` (gitignored). Clean up `__pycache__/` when done.
