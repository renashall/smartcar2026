---
name: pi-access
description: Drive and test this Freenove smart-car repo on the real Raspberry Pi over SSH. Use when asked to test/run/screenshot anything on the Pi, sync local code to the car, exercise hardware (motors, servo, LEDs, ultrasonic, camera, line sensors, ADC), or automate the server/client GUIs (click buttons, type, capture the desktop). The toolkit lives in Internal_Debug/tools/ (local-only, git-ignored).
---

# Raspberry Pi access workflow

A local toolkit (`Internal_Debug/tools/`) for driving the real Pi car over SSH:
force-sync code, screenshot the desktop, automate the Qt GUIs with mouse/keyboard,
and run/control the server, client, lessons, and hardware.

> `Internal_Debug/` is git-ignored (`.gitignore` has `*Internal_Debug`), so the
> SSH credentials and tools never get committed. Never paste the password or key
> into a tracked file. If `Internal_Debug/info` or `Internal_Debug/.ssh_key` is
> missing, run `setup-access.sh` (one time) before anything else.

## Always

- Run tools from the **repo root** (`cd /c/Users/lindi/GitHub/smartcar2026`). The
  Bash working dir can drift; if a path doubles up (`Internal_Debug/Internal_Debug/...`),
  you forgot to cd back.
- **`sync.sh` before every test** — local edits do NOT magically reach the Pi.
- After any driving/autonomous test, **stop the motors** as a safety net:
  `python3 -c 'import sys;sys.path.insert(0,"/home/pi/smartcar2026/Code/Server");from Motor import Motor;Motor().setMotorModel(0,0,0,0)'`

## Tools (`Internal_Debug/tools/`)

| Command | Use |
|---|---|
| `bash Internal_Debug/tools/setup-access.sh` | One-time: install SSH key on the Pi + Pi-side packages (scrot, xdotool, grim, ydotool, imagemagick, picamera2). Idempotent. |
| `bash Internal_Debug/tools/sync.sh` | Force-push `Code/`, setup scripts, requirements to `~/smartcar2026`. Run before every test. |
| `bash Internal_Debug/tools/pi.sh '<cmd>'` | Run any command on the Pi. |
| `bash Internal_Debug/tools/screenshot.sh [name]` | Capture the desktop (scrot on X11 / grim on Wayland), pull the PNG, print its local path. Then Read the PNG to view it. |
| `bash Internal_Debug/tools/click.sh X Y [btn]` / `type.sh "txt"` / `key.sh <keys>` | Mouse/keyboard automation (X11/xdotool). |
| `bash Internal_Debug/tools/server.sh {start [headless\|gui]\|stop\|status\|log}` | Control the car server. `headless` = `main.py -tn`. Logs to `/tmp/smartcar_server.log`. |
| `bash Internal_Debug/tools/client.sh {start [ip]\|stop\|status\|log}` | Control the client GUI (no sudo). |
| `bash Internal_Debug/tools/smoke-test.sh` | Sync + verify imports + camera + start server + check ports 5000/8000. |

## GUI automation: coordinate model

Qt widgets in `*_Ui.py` use absolute `setGeometry(x, y, w, h)`. A control's
**screen** click point = `window_origin + (x + w/2, y + h/2)`. Get the window
origin live:
`bash Internal_Debug/tools/pi.sh "export DISPLAY=:0 XAUTHORITY=\$HOME/.Xauthority; xdotool search --name freenove getwindowgeometry --shell %@"`
Do NOT eyeball coordinates from a scaled screenshot — derive them from the `.py`
geometry, or crop the window region with ImageMagick (`convert full.png -crop WxH+X+Y`)
for a true-scale view.

## Gotchas (these will bite)

- **pkill self-match:** `pkill -f 'python3 main.py'` matches its own SSH shell and
  kills the session (exit 255). Always use the bracket trick: `pkill -f '[p]ython3 main.py'`.
- **Detaching GUIs over SSH:** plain `nohup ... &` dies. Use
  `setsid <cmd> >log 2>&1 </dev/null &`.
- **Black screenshot** = the desktop is on Wayland (rootless Xwayland root is
  black to scrot). This repo runs the Pi on **X11** (`raspi-config nonint do_wayland W1`),
  which is required for both RealVNC and xdotool.
- **Buffered logs:** run server/Python with `python3 -u` so `print()` shows live.
- **One camera user at a time:** stop the server/lesson holding the camera before
  starting another.
- **Motor PWM latches:** killing a driving process with SIGTERM leaves the wheels
  spinning. Use `timeout --signal=INT` so the `finally`/cleanup runs, then the
  safety motor-stop above.

## What "working" means

1. Imports resolve from `/usr/lib/python3/dist-packages` (apt), not `/usr/local` (broken pip).
2. `rpicam-hello --list-cameras` lists the camera; `picamera2` opens without error.
3. Server listens on **5000** (commands) + **8000** (video) on all interfaces.
4. Clicking client controls logs `CMD_*` server-side; with the car battery
   powered (~7-8 V), they physically move the car.
5. RealVNC Viewer shows the desktop (needs X11 + a forced resolution).

See `Internal_Debug/AGENTS.md` for the discovered Pi specifics (model, OS, paths).
