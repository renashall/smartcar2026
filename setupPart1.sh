#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find_package_dir() {
  current_dir="$SCRIPT_DIR"

  while [ "$current_dir" != "/" ]; do
    if [ -f "$current_dir/Code/build.sh" ] &&
      [ -f "$current_dir/Code/setup.py" ] &&
      [ -f "$current_dir/Code/Patch/patch_for_bullseye.sh" ]; then
      PACKAGE_DIR="$current_dir"
      return
    fi

    if [ "$(basename "$current_dir")" = "Code" ] &&
      [ -f "$current_dir/build.sh" ] &&
      [ -f "$current_dir/setup.py" ] &&
      [ -f "$current_dir/Patch/patch_for_bullseye.sh" ]; then
      PACKAGE_DIR="$(dirname "$current_dir")"
      return
    fi

    current_dir="$(dirname "$current_dir")"
  done

  echo "Could not find the Freenove package folder."
  echo "Place this script in the Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi folder or its Code folder."
  exit 1
}

ask_pi_model() {
  echo "Which Raspberry Pi are you using?"
  echo "1) Raspberry Pi 4B"
  echo "2) Raspberry Pi 400"
  echo "3) Raspberry Pi 3B+"
  echo "4) Raspberry Pi 3B"
  echo "5) Other"

  while true; do
    read -r -p "Enter 1-5: " choice
    case "$choice" in
      1) PI_MODEL="4B"; break ;;
      2) PI_MODEL="400"; break ;;
      3) PI_MODEL="3B+"; break ;;
      4) PI_MODEL="3B"; break ;;
      5) PI_MODEL="Other"; break ;;
      *) echo "Please enter a number from 1 to 5." ;;
    esac
  done
}

ask_os_date() {
  echo
  echo "Is your Raspberry Pi OS image dated 2021-10-30 or later?"
  echo "1) Yes, 2021-10-30 or later"
  echo "2) No, earlier than 2021-10-30"
  echo "3) Not sure"

  while true; do
    read -r -p "Enter 1-3: " choice
    case "$choice" in
      1) OS_20211030_OR_LATER="yes"; break ;;
      2) OS_20211030_OR_LATER="no"; break ;;
      3) OS_20211030_OR_LATER="unknown"; break ;;
      *) echo "Please enter a number from 1 to 3." ;;
    esac
  done
}

run_raspi_config() {
  if command -v raspi-config >/dev/null 2>&1; then
    sudo raspi-config nonint "$@" || true
  else
    echo "raspi-config was not found; skipping raspi-config $*"
  fi
}

# raspi-config's nonint getters echo "0" when the interface is already enabled
# and "1" when it is disabled. Returns success only when it is already enabled.
interface_enabled() {
  getter="$1"
  if command -v raspi-config >/dev/null 2>&1; then
    [ "$(sudo raspi-config nonint "$getter" 2>/dev/null)" = "0" ]
  else
    return 1
  fi
}

# Enable an interface only if it is not already on, so re-running the script
# does not needlessly toggle interfaces that are already configured.
ensure_interface_enabled() {
  name="$1"    # human-friendly label, e.g. VNC
  getter="$2"  # raspi-config getter, e.g. get_vnc
  setter="$3"  # raspi-config setter, e.g. do_vnc

  if interface_enabled "$getter"; then
    echo "$name is already enabled; leaving it unchanged."
  else
    echo "Enabling $name..."
    run_raspi_config "$setter" 0
  fi
}

# A headless Pi has no monitor, so after a reboot the VNC server has no display
# to share and RealVNC shows "Cannot currently show the desktop". Booting into
# the desktop and giving VNC a virtual screen resolution fixes this. Both are
# plain raspi-config calls, so no manual config.txt editing is needed.
configure_headless_vnc() {
  echo
  echo "Setting up the desktop and a virtual screen so VNC works without a monitor..."

  # Boot straight into the desktop and log in automatically so a desktop
  # session exists for VNC to share after every reboot (B4 = desktop autologin).
  run_raspi_config do_boot_behaviour B4

  # Give the VNC server a virtual screen resolution to use when no monitor is
  # attached. Without this, a headless Pi cannot show a desktop over VNC.
  run_raspi_config do_vnc_resolution 1280x720

  # Apply the new resolution now by restarting the VNC service (it also starts
  # on the next reboot).
  sudo systemctl restart vncserver-x11-serviced.service >/dev/null 2>&1 || true
}

enable_interfaces() {
  echo
  echo "Checking SSH, VNC, and I2C..."
  ensure_interface_enabled "SSH" get_ssh do_ssh
  ensure_interface_enabled "VNC" get_vnc do_vnc
  ensure_interface_enabled "I2C" get_i2c do_i2c

  sudo systemctl enable --now ssh >/dev/null 2>&1 || true
  sudo systemctl enable --now vncserver-x11-serviced.service >/dev/null 2>&1 || true

  echo "Installing I2C tools and Python SMBus support..."
  sudo apt-get update
  sudo apt-get install -y i2c-tools python3-smbus git

  echo "Checking I2C bus 1. It is OK if no devices appear until the car board is connected."
  sudo i2cdetect -y 1 || true
}

configure_camera_interface() {
  echo
  case "$OS_20211030_OR_LATER" in
    yes)
      echo "OS is 2021-10-30 or later. Disabling the legacy Camera interface if that option exists..."
      run_raspi_config do_camera 1
      run_raspi_config do_legacy 1
      ;;
    no)
      echo "OS is earlier than 2021-10-30. Enabling the Camera interface if that option exists..."
      run_raspi_config do_camera 0
      run_raspi_config do_legacy 0
      ;;
    unknown)
      echo "OS date is unknown. Leaving the Camera interface unchanged."
      echo "If your OS is earlier than 2021-10-30, enable Camera manually."
      echo "If your OS is 2021-10-30 or later, disable Camera manually."
      ;;
  esac
}

make_python3_default() {
  echo
  echo "Checking the default python command..."

  if command -v python >/dev/null 2>&1; then
    python_major="$(python -c 'import sys; print(sys.version_info[0])' 2>/dev/null || echo unknown)"
  else
    python_major="missing"
  fi

  if [ "$python_major" = "3" ]; then
    echo "python already opens Python 3."
    return
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 was not found. Installing python3..."
    sudo apt-get install -y python3
  fi

  echo "Setting /usr/bin/python to point to python3..."
  if [ -e /usr/bin/python ] || [ -L /usr/bin/python ]; then
    sudo rm -f /usr/bin/python
  fi
  sudo ln -s /usr/bin/python3 /usr/bin/python

  python -c 'import sys; print("python now opens Python " + sys.version.split()[0])'
}

check_project_files() {
  echo
  echo "Checking Freenove project files..."

  if [ ! -d "$PACKAGE_DIR/Code" ]; then
    echo "Code folder was not found at:"
    echo "$PACKAGE_DIR/Code"
    exit 1
  fi

  echo "Using local Freenove package folder:"
  echo "$PACKAGE_DIR"
  echo "No files will be downloaded or recloned."
}

apply_bullseye_patch() {
  echo
  patch_dir="$PACKAGE_DIR/Code/Patch"
  patch_script="$patch_dir/patch_for_bullseye.sh"

  if [ ! -f "$patch_script" ]; then
    echo "Patch script was not found at:"
    echo "$patch_script"
    echo "Skipping patch."
    return
  fi

  echo "Running Bullseye patch..."
  (
    cd "$patch_dir"
    sudo sh ./patch_for_bullseye.sh
  )
}

find_package_dir
ask_pi_model
ask_os_date

echo
echo "Using Freenove package folder: $PACKAGE_DIR"
echo "Selected Raspberry Pi model: $PI_MODEL"
echo "Selected OS date option: $OS_20211030_OR_LATER"

enable_interfaces
configure_headless_vnc
configure_camera_interface
make_python3_default
check_project_files
apply_bullseye_patch

echo
read -r -p "Hit Enter to reboot"
sudo reboot
