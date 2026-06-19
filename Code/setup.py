#!/usr/bin/env python3
"""One-command environment setup for the
"Machine Learning with Raspberry Pi & Smart Car" course.

What this does:
  1. Detects your operating system (Windows, macOS, or Linux).
  2. Creates a virtual environment named ".venv" in this project's root folder.
  3. Installs the Python packages listed in requirements.txt into that .venv.

This is for LAPTOPS and DESKTOPS -- the machines that run the camera viewer,
face-detection, and GUI lessons (Lesson 6 client, 7, 8, 11). On the Raspberry
Pi itself, run Code/setupPart1.sh and Code/setupPart2.sh instead; they install
the system packages the car hardware needs, and a .venv would hide them.

How to run it (use your normal system Python -- NOT inside a .venv):

    Windows:        python Code/setup.py
    macOS / Linux:  python3 Code/setup.py

You can also run it from inside the Code folder:

    Windows:        cd Code && python setup.py
    macOS / Linux:  cd Code && python3 setup.py

You do NOT need administrator or sudo for this. It only creates a .venv folder
inside this project; it does not touch system Python. Useful options:

    --force    delete and rebuild an existing .venv
    --pi       set up the .venv anyway, even on a Raspberry Pi

If anything fails, the script prints exactly what to try by hand.

Note: this file uses plain snake_case (PEP 8) to match the rest of this
teaching repo and stay readable for students.
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = REPO_ROOT / ".venv"
REQUIREMENTS = REPO_ROOT / "requirements.txt"


def detect_os():
    """Return a friendly OS name: 'Windows', 'macOS', 'Linux', or the raw value."""
    system = platform.system()
    return {"Windows": "Windows", "Darwin": "macOS", "Linux": "Linux"}.get(system, system)


def is_raspberry_pi():
    """Best-effort check for whether we are running on a Raspberry Pi."""
    if platform.system() != "Linux":
        return False
    model = Path("/proc/device-tree/model")
    if model.exists():
        try:
            if "raspberry pi" in model.read_text(errors="ignore").lower():
                return True
        except OSError:
            pass
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        try:
            text = cpuinfo.read_text(errors="ignore").lower()
            if "raspberry pi" in text or "bcm2" in text:
                return True
        except OSError:
            pass
    return False


def venv_python(venv_dir):
    """Path to the Python interpreter inside the given virtual environment."""
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def run(cmd, **kwargs):
    """Run a command, streaming its output. Return True on success."""
    print("    $ " + " ".join(str(part) for part in cmd))
    # Flush so our message lands before the subprocess's own output, even when
    # this script's stdout is piped to a file or another program.
    sys.stdout.flush()
    result = subprocess.run(cmd, **kwargs)
    return result.returncode == 0


def create_venv(force):
    """Create the .venv, returning True on success."""
    if VENV_DIR.exists():
        if force:
            print(f"Removing existing virtual environment at {VENV_DIR} ...")
            shutil.rmtree(VENV_DIR, ignore_errors=True)
        else:
            print(f"A virtual environment already exists at {VENV_DIR}.")
            print("Reusing it. Pass --force to delete and rebuild it from scratch.")
            return True

    print(f"Creating virtual environment at {VENV_DIR} ...")
    if run([sys.executable, "-m", "venv", str(VENV_DIR)]):
        return True

    print()
    print("Could not create the virtual environment.")
    print("On Debian/Ubuntu/Raspberry Pi OS the 'venv' module ships separately;")
    print("install it and run this script again:")
    print("    sudo apt update && sudo apt install -y python3-venv")
    print("On Windows/macOS, make sure you installed Python from python.org.")
    return False


def install_requirements():
    """Upgrade pip and install requirements.txt into the .venv. Return True on success."""
    python = venv_python(VENV_DIR)
    if not python.exists():
        print(f"Could not find the virtual environment's Python at {python}.")
        return False

    if not REQUIREMENTS.exists():
        print(f"No requirements.txt found at {REQUIREMENTS}; nothing to install.")
        return True

    print("Upgrading pip inside the virtual environment ...")
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])

    print(f"Installing packages from {REQUIREMENTS.name} ...")
    if run([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)]):
        return True

    print()
    print("Some packages did not install. You can try again by hand with:")
    print(f"    {python} -m pip install -r {REQUIREMENTS}")
    return False


def print_next_steps():
    """Tell the user how to activate the .venv and run a lesson."""
    print()
    print("=" * 64)
    print("Setup complete. Your virtual environment is at .venv")
    print("=" * 64)
    print()
    print("To use it, activate it in your terminal:")
    print()
    if platform.system() == "Windows":
        print("  PowerShell:")
        print("    .\\.venv\\Scripts\\Activate.ps1")
        print("    python Code\\User\\lesson_7_face_tracking.py <PI_IP>")
        print()
        print("  If PowerShell blocks the activation script, allow it once with:")
        print("    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned")
        print()
        print("  Command Prompt (cmd):")
        print("    .venv\\Scripts\\activate.bat")
        print()
        print("  Or skip activation and call the venv's Python directly:")
        print("    .venv\\Scripts\\python.exe Code\\User\\lesson_7_face_tracking.py <PI_IP>")
    else:
        print("    source .venv/bin/activate")
        print("    python3 Code/User/lesson_7_face_tracking.py <PI_IP>")
        print()
        print("  Or skip activation and call the venv's Python directly:")
        print("    .venv/bin/python Code/User/lesson_7_face_tracking.py <PI_IP>")
    print()
    print("Replace <PI_IP> with your Raspberry Pi's IP address. Run 'deactivate'")
    print("to leave the virtual environment when you are done.")


def main():
    parser = argparse.ArgumentParser(
        description="Create a .venv and install the course Python packages."
    )
    parser.add_argument(
        "--force", action="store_true", help="delete and rebuild an existing .venv"
    )
    parser.add_argument(
        "--pi", action="store_true",
        help="set up the .venv even when running on a Raspberry Pi",
    )
    args = parser.parse_args()

    os_name = detect_os()
    print(f"Detected operating system: {os_name} (Python {platform.python_version()})")
    print(f"Project folder: {REPO_ROOT}")

    if is_raspberry_pi() and not args.pi:
        print()
        print("This looks like a Raspberry Pi.")
        print("On the Pi, DON'T use this .venv installer -- run the two setup")
        print("scripts instead, which install the system packages the car needs:")
        print("    cd Code")
        print("    chmod +x setupPart1.sh setupPart2.sh")
        print("    ./setupPart1.sh   # then reboot")
        print("    ./setupPart2.sh   # then reboot")
        print()
        print("If you really want a .venv on the Pi anyway, re-run with --pi.")
        return 0

    if not create_venv(args.force):
        return 1
    if not install_requirements():
        return 1

    print_next_steps()
    return 0


if __name__ == "__main__":
    sys.exit(main())
