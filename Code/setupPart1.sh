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

  echo "Could not find the smartcar2026 package folder."
  echo "Place this script in the smartcar2026 folder or its Code folder."
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

run_raspi_config() {
  if command -v raspi-config >/dev/null 2>&1; then
    set +e
    sudo raspi-config nonint "$@"
    status="$?"
    set -e

    if [ "$status" -eq 130 ]; then
      echo "Interrupted while running raspi-config $*."
      exit 130
    fi

    if [ "$status" -ne 0 ]; then
      echo "raspi-config $* failed or is unsupported on this OS; continuing."
    fi
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
# to share and RealVNC shows "Cannot currently show the desktop". Configure the
# desktop backend and virtual screen only through raspi-config so the OS owns
# the underlying VNC/session files.
configure_headless_vnc() {
  echo
  echo "Setting up the desktop and a virtual screen so VNC works without a monitor..."

  # Boot straight into the desktop and log in automatically so a desktop
  # session exists for VNC to share after every reboot (B4 = desktop autologin).
  run_raspi_config do_boot_behaviour B4

  # RealVNC's screen sharing cannot capture the Wayland desktop (labwc/wayfire)
  # that Raspberry Pi OS Bookworm uses by default, so VNC shows a black screen
  # or "Cannot currently show the desktop". Switch the desktop to X11, which
  # RealVNC can share. do_wayland W1 = "Openbox with X11 backend"; it is
  # idempotent (no-op if already X11) and simply skipped where unsupported.
  # (Note: this raspi-config has no get_wayland getter, so we just set it.)
  if command -v raspi-config >/dev/null 2>&1; then
    echo "Selecting the X11 desktop backend (do_wayland W1) so VNC can share it..."
    run_raspi_config do_wayland W1
  fi

  # Give the VNC server a virtual screen resolution to use when no monitor is
  # attached. Ignored on OS versions that do not support it.
  run_raspi_config do_vnc_resolution 1280x720
}

enable_interfaces() {
  echo
  echo "Checking SSH, VNC, and I2C..."
  ensure_interface_enabled "SSH" get_ssh do_ssh
  ensure_interface_enabled "VNC" get_vnc do_vnc
  ensure_interface_enabled "I2C" get_i2c do_i2c

  sudo systemctl enable --now ssh >/dev/null 2>&1 || true

  echo "Installing I2C tools and Python SMBus support..."
  sudo apt-get update
  sudo apt-get install -y i2c-tools python3-smbus git

  echo "Checking I2C bus 1. It is OK if no devices appear until the car board is connected."
  sudo i2cdetect -y 1 || true
}

configure_camera_interface() {
  echo
  case "$CAMERA_STACK" in
    libcamera)
      echo "OS uses the libcamera camera stack (picamera2); the legacy camera is not needed."
      # Make sure the legacy camera is OFF so libcamera stays active. This is a
      # no-op on Bookworm, where the legacy option has been removed.
      run_raspi_config do_legacy 1
      ;;
    legacy)
      echo "OS uses the legacy camera stack. Enabling the Camera interface..."
      run_raspi_config do_camera 0
      run_raspi_config do_legacy 0
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
  # The patch swaps in a legacy MMAL (libmmal.so) library, which only exists on
  # the legacy 32-bit camera stack. On libcamera systems (Bullseye/Bookworm with
  # picamera2) it is unnecessary and the target files do not exist, so skip it.
  if [ "$CAMERA_STACK" != "legacy" ]; then
    echo "Skipping the legacy libmmal patch (not needed with the libcamera stack)."
    return
  fi

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
detect_environment
print_detection

echo
echo "Using Freenove package folder: $PACKAGE_DIR"

enable_interfaces
configure_headless_vnc
configure_camera_interface
make_python3_default
check_project_files
apply_bullseye_patch

echo
read -r -p "Hit Enter to reboot"
sudo reboot
