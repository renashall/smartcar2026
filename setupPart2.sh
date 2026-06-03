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
      1) PI_MODEL="4B"; DISABLE_AUDIO="no"; break ;;
      2) PI_MODEL="400"; DISABLE_AUDIO="no"; break ;;
      3) PI_MODEL="3B+"; DISABLE_AUDIO="yes"; break ;;
      4) PI_MODEL="3B"; DISABLE_AUDIO="yes"; break ;;
      5) PI_MODEL="Other"; DISABLE_AUDIO="yes"; break ;;
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

find_config_file() {
  if [ -f /boot/config.txt ]; then
    CONFIG_FILE="/boot/config.txt"
  elif [ -f /boot/firmware/config.txt ]; then
    CONFIG_FILE="/boot/firmware/config.txt"
  else
    CONFIG_FILE="/boot/config.txt"
  fi
}

backup_config_file() {
  if [ -f "$CONFIG_FILE" ]; then
    backup_file="$CONFIG_FILE.lesson0-backup.$(date +%Y%m%d-%H%M%S)"
    echo "Creating backup: $backup_file"
    sudo cp "$CONFIG_FILE" "$backup_file"
  fi
}

set_config_value() {
  key="$1"
  value="$2"

  sudo sed -i "/^${key}=.*/d" "$CONFIG_FILE"
  printf '%s=%s\n' "$key" "$value" | sudo tee -a "$CONFIG_FILE" >/dev/null
}

edit_camera_config() {
  echo
  echo "Editing camera config in $CONFIG_FILE..."
  sudo touch "$CONFIG_FILE"

  sudo sed -i 's/^camera_auto_detect=1/# camera_auto_detect=1/' "$CONFIG_FILE"

  set_config_value start_x 1
  set_config_value gpu_mem 128

  if [ "$OS_20211030_OR_LATER" = "no" ]; then
    echo "Earlier OS selected. If camera_auto_detect is not present, that is expected."
  fi
}

disable_audio_for_older_pi_models() {
  echo
  if [ "$DISABLE_AUDIO" != "yes" ]; then
    echo "Raspberry Pi $PI_MODEL selected. Skipping older-model audio workaround."
    return
  fi

  echo "Applying audio workaround for Raspberry Pi $PI_MODEL..."

  sudo mkdir -p /etc/modprobe.d
  if [ -f /etc/modprobe.d/snd-blacklist.conf ] &&
    sudo grep -qxF 'blacklist snd_bcm2835' /etc/modprobe.d/snd-blacklist.conf; then
    echo "snd_bcm2835 is already blacklisted."
  else
    echo 'blacklist snd_bcm2835' | sudo tee -a /etc/modprobe.d/snd-blacklist.conf >/dev/null
  fi

  sudo sed -i 's/^dtparam=audio=on/# dtparam=audio=on/' "$CONFIG_FILE"
}

install_car_libraries() {
  echo
  code_dir="$PACKAGE_DIR/Code"

  if [ ! -d "$code_dir" ]; then
    echo "Freenove code folder was not found at:"
    echo "$code_dir"
    echo "Make sure this script is inside the downloaded Freenove package folder or its Code folder."
    exit 1
  fi

  echo "Installing car libraries from $code_dir..."
  (
    cd "$code_dir"
    sh ./build.sh
    sudo python3 setup.py
  )
}

install_course_python_packages() {
  echo
  echo "Installing the Python packages used in the lessons..."
  echo "(NumPy, OpenCV, Pillow, PyQt5, and the Pi camera library.)"

  sudo apt-get update || true

  # Prefer apt on the Pi: these prebuilt packages install far faster and more
  # reliably than building wheels with pip. Each one is installed on its own so
  # a single missing package never blocks the rest.
  for pkg in python3-numpy python3-opencv python3-pil python3-pyqt5 python3-picamera; do
    echo "  - $pkg"
    sudo apt-get install -y "$pkg" || echo "    (could not install $pkg with apt; continuing)"
  done

  # Fallback: install anything still missing from requirements.txt with pip.
  req_file="$PACKAGE_DIR/requirements.txt"
  if [ -f "$req_file" ]; then
    echo "Checking requirements.txt with pip for anything still missing..."
    sudo pip3 install -r "$req_file" 2>/dev/null \
      || sudo pip3 install --break-system-packages -r "$req_file" 2>/dev/null \
      || echo "pip step skipped; the apt packages above are normally enough."
  fi

  echo "Lesson Python packages are ready."
}

find_package_dir
ask_pi_model
ask_os_date
find_config_file

echo
echo "Using Freenove package folder: $PACKAGE_DIR"
echo "Selected Raspberry Pi model: $PI_MODEL"
echo "Selected OS date option: $OS_20211030_OR_LATER"
echo "Using config file: $CONFIG_FILE"

backup_config_file
edit_camera_config
disable_audio_for_older_pi_models
install_car_libraries
install_course_python_packages

echo
read -r -p "Hit Enter to reboot"
sudo reboot
