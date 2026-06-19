#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find_package_dir() {
  current_dir="$SCRIPT_DIR"

  while [ "$current_dir" != "/" ]; do
    if [ -f "$current_dir/Code/Server/main.py" ] &&
      [ -f "$current_dir/Code/Patch/patch_for_bullseye.sh" ]; then
      PACKAGE_DIR="$current_dir"
      return
    fi

    if [ "$(basename "$current_dir")" = "Code" ] &&
      [ -f "$current_dir/Server/main.py" ] &&
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

# Detect the Raspberry Pi model, OS, architecture, and camera stack instead of
# asking the user. Every other function reads the variables this sets.
detect_environment() {
  # --- Raspberry Pi model ---
  PI_MODEL_RAW="Unknown"
  if [ -r /proc/device-tree/model ]; then
    # The device-tree model string is NUL-terminated, so strip the trailing NUL.
    PI_MODEL_RAW="$(tr -d '\0' < /proc/device-tree/model)"
  elif [ -r /proc/cpuinfo ]; then
    PI_MODEL_RAW="$(grep -m1 -i '^Model' /proc/cpuinfo | cut -d: -f2- | sed 's/^[[:space:]]*//')"
  fi

  case "$PI_MODEL_RAW" in
    *"Raspberry Pi 5"*)              PI_MODEL="5" ;;
    *"Raspberry Pi 400"*)            PI_MODEL="400" ;;
    *"Raspberry Pi 4"*)              PI_MODEL="4B" ;;
    *"Raspberry Pi 3 Model B Plus"*) PI_MODEL="3B+" ;;
    *"Raspberry Pi 3"*)              PI_MODEL="3B" ;;
    *"Raspberry Pi 2"*)              PI_MODEL="2B" ;;
    *"Raspberry Pi Zero"*)           PI_MODEL="Zero" ;;
    *)                               PI_MODEL="Other" ;;
  esac

  # Older models need the buzzer/audio workaround; the Pi 4 / 400 / 5 do not.
  case "$PI_MODEL" in
    4B|400|5) DISABLE_AUDIO="no" ;;
    *)        DISABLE_AUDIO="yes" ;;
  esac

  # --- Operating system (Bookworm / Bullseye / Buster / ...) ---
  OS_CODENAME="unknown"
  OS_VERSION_ID="unknown"
  OS_PRETTY="unknown"
  if [ -r /etc/os-release ]; then
    # shellcheck source=/dev/null
    . /etc/os-release
    OS_CODENAME="${VERSION_CODENAME:-unknown}"
    OS_VERSION_ID="${VERSION_ID:-unknown}"
    OS_PRETTY="${PRETTY_NAME:-unknown}"
  fi

  # --- User-space architecture: 32-bit (armhf) or 64-bit (arm64) ---
  KERNEL_ARCH="$(uname -m 2>/dev/null || echo unknown)"
  if command -v getconf >/dev/null 2>&1; then
    OS_BITS="$(getconf LONG_BIT 2>/dev/null || echo unknown)"
  else
    case "$KERNEL_ARCH" in
      aarch64|arm64) OS_BITS="64" ;;
      armv6l|armv7l) OS_BITS="32" ;;
      *)             OS_BITS="unknown" ;;
    esac
  fi
  if command -v dpkg >/dev/null 2>&1; then
    DPKG_ARCH="$(dpkg --print-architecture 2>/dev/null || echo unknown)"
  else
    DPKG_ARCH="unknown"
  fi

  # --- Camera stack: legacy (MMAL/picamera) vs libcamera (picamera2) ---
  # Buster and earlier use the legacy camera stack; Bullseye and Bookworm use
  # libcamera with picamera2. This drives every camera-related decision below.
  case "$OS_CODENAME" in
    bookworm|trixie|bullseye) CAMERA_STACK="libcamera" ;;
    buster|stretch|jessie)    CAMERA_STACK="legacy" ;;
    *)
      # Unknown OS: assume a modern libcamera system, the safe default on any
      # current Raspberry Pi OS image.
      CAMERA_STACK="libcamera"
      ;;
  esac
}

print_detection() {
  echo
  echo "Detected environment:"
  echo "  Raspberry Pi : $PI_MODEL ($PI_MODEL_RAW)"
  echo "  OS           : $OS_PRETTY [codename: $OS_CODENAME, version: $OS_VERSION_ID]"
  echo "  Architecture : ${OS_BITS}-bit (kernel $KERNEL_ARCH, dpkg $DPKG_ARCH)"
  echo "  Camera stack : $CAMERA_STACK"
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
  echo "Configuring the camera in $CONFIG_FILE for the $CAMERA_STACK stack..."
  sudo touch "$CONFIG_FILE"

  case "$CAMERA_STACK" in
    libcamera)
      # libcamera / picamera2 needs camera auto-detect ON and must NOT use the
      # legacy firmware camera settings. Remove any legacy leftovers (including
      # from an earlier run of this script) so they cannot block the camera.
      sudo sed -i '/^[# ]*start_x=.*/d' "$CONFIG_FILE"
      sudo sed -i '/^[# ]*gpu_mem=.*/d' "$CONFIG_FILE"
      sudo sed -i '/^[# ]*camera_auto_detect=.*/d' "$CONFIG_FILE"
      printf 'camera_auto_detect=1\n' | sudo tee -a "$CONFIG_FILE" >/dev/null
      echo "Set camera_auto_detect=1 and removed legacy start_x / gpu_mem."
      ;;
    legacy)
      # Legacy camera firmware: enable start_x and a GPU memory split, and turn
      # off the newer auto-detect line if it is present.
      sudo sed -i 's/^camera_auto_detect=1/# camera_auto_detect=1/' "$CONFIG_FILE"
      set_config_value start_x 1
      set_config_value gpu_mem 128
      echo "Enabled legacy camera (start_x=1, gpu_mem=128)."
      ;;
  esac
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

  # This used to run Code/build.sh + Code/setup.py. Those helper files were
  # removed; the only car-specific thing they installed is the WS281x driver for
  # the addressable LED strip, so install it directly here. (python3-pyqt5 and
  # the other lesson packages are handled by install_course_python_packages.)
  echo "Installing the addressable-LED (WS281x) driver used by the car..."
  sudo apt-get install -y python3-dev || true

  if sudo apt-get install -y python3-rpi-ws281x 2>/dev/null; then
    echo "Installed rpi_ws281x from apt."
  elif command -v pip3 >/dev/null 2>&1 &&
    sudo pip3 install rpi_ws281x --break-system-packages; then
    echo "Installed rpi_ws281x from pip."
  else
    echo "Could not install rpi_ws281x automatically."
    echo "If the LED lessons fail, install it by hand with:"
    echo "  sudo pip3 install rpi_ws281x --break-system-packages"
  fi
}

install_course_python_packages() {
  echo
  echo "Installing the Python packages used in the lessons..."
  echo "(NumPy, OpenCV, Pillow, PyQt5, and the Pi camera library.)"

  sudo apt-get update || true

  # Pick the camera library that matches this OS's camera stack: picamera2 for
  # libcamera systems (Bullseye/Bookworm), legacy picamera for Buster/earlier.
  if [ "$CAMERA_STACK" = "legacy" ]; then
    camera_pkg="python3-picamera"
  else
    camera_pkg="python3-picamera2"
  fi

  # Prefer apt on the Pi: these prebuilt packages install far faster and more
  # reliably than building wheels with pip. Each one is installed on its own so
  # a single missing package never blocks the rest.
  for pkg in python3-numpy python3-opencv python3-pil python3-pyqt5 "$camera_pkg"; do
    echo "  - $pkg"
    sudo apt-get install -y "$pkg" || echo "    (could not install $pkg with apt; continuing)"
  done

  # Deliberately NO pip fallback here. On the Pi, pip-installing numpy / opencv /
  # etc. into /usr/local shadows the working apt packages with copies that often
  # build incompletely, which breaks imports like:
  #   "ImportError: Error importing numpy ... import numpy from its source dir".
  # The apt packages above are the supported set; requirements.txt is only for
  # separate (non-Pi) computers.

  # Self-heal: remove any pip-installed copies of these libraries that a previous
  # setup may have left in /usr/local. They shadow the apt versions and often
  # fail to import (e.g. numpy missing libopenblas.so.0). On the Pi these must
  # come from apt, so dropping the pip copies is always the right move.
  if command -v pip3 >/dev/null 2>&1; then
    echo "Removing any pip-installed copies that would shadow the apt packages..."
    for pip_pkg in numpy opencv-python opencv-contrib-python Pillow PyQt5; do
      sudo pip3 uninstall -y "$pip_pkg" --break-system-packages >/dev/null 2>&1 || true
    done
  fi

  # Verify the key modules actually import, so a problem shows up here instead of
  # halfway through a lesson.
  echo "Verifying the lesson Python packages import correctly..."
  if python3 - <<'PY'
import importlib.util, sys
modules = ["numpy", "cv2", "PIL", "PyQt5"]
missing = [m for m in modules if importlib.util.find_spec(m) is None]
if missing:
    print("  Missing/broken modules:", ", ".join(missing))
    sys.exit(1)
import numpy
print("  numpy", numpy.__version__, "from", numpy.__file__)
print("  all core lesson modules import OK")
PY
  then
    echo "Lesson Python packages are ready."
  else
    echo "Some packages did not import. Make sure none were pip-installed into"
    echo "/usr/local (which shadows the apt versions). To clean that up, run:"
    echo "  sudo pip3 uninstall -y numpy opencv-python Pillow PyQt5 --break-system-packages"
  fi
}

find_package_dir
detect_environment
find_config_file
print_detection

echo
echo "Using Freenove package folder: $PACKAGE_DIR"
echo "Using config file: $CONFIG_FILE"

backup_config_file
edit_camera_config
disable_audio_for_older_pi_models
install_car_libraries
install_course_python_packages

echo
read -r -p "Hit Enter to reboot"
sudo reboot
