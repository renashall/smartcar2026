# Machine Learning with Raspberry Pi & Smart Car (Level 3)

This repository was created by **AI Code Academy** for the **Machine Learning with Raspberry Pi & Smart Car (Level 3)** course. It contains the course code files, resources, setup scripts and instructions, plus examples and projects for each lesson.

## Freenove 4WD Smart Car Kit for Raspberry Pi

> **Notice: Updated by AI Code Academy**

**AI Code Academy** has adapted this repository for the **Machine Learning with Raspberry Pi & Smart Car (Level 3)** course. The Freenove project files are still present; some have been updated or rewritten to modernize and clean up the code and make it more user friendly and efficient. Changes to the core car code also support Raspberry Pi 5 hardware where possible. See [CHANGES.md](CHANGES.md) for the changes from Freenove's version.

<img src='Resources/icon.png' width='30%'/>

### Requirements - Hardware

Gather the car parts and a way to prepare the Raspberry Pi before starting. A separate computer is needed to flash the microSD card with Raspberry Pi Imager, but running the client lessons on that computer is optional.

- **Computer:** A Windows, macOS, or Linux laptop or desktop for flashing Raspberry Pi OS, and remotely accessing the Pi via methods like remote desktop control or SSH.
- **Raspberry Pi:** A Raspberry Pi 3B/3B+, 4B, or 5.
  - **MicroSD Card:** 32 GB or larger for Raspberry Pi OS.
  - **MicroSD Card Reader:** Built into the computer or connected by external USB adapter. Used for flashing the microSD card.
  - **AC Power Adapter:** Match the Pi model's power connector and output. See [Raspberry Pi's power supply guidance](https://www.raspberrypi.com/documentation/computers/getting-started.html#power).
    - **Pi 3:** Micro-USB, 5 V/2.5 A (12.5 W).
    - **Pi 4:** USB-C, 5 V/3 A (15 W).
    - **Pi 5:** USB-C, 5 V/5 A (25 W).
- **Smart Car Kit:** The Freenove 4WD Smart Car Kit for Raspberry Pi.
- **Car Batteries & Charger:** Two 18650 batteries and a charger suitable for those batteries. Read [About_Battery.pdf](Resources/About_Battery.pdf) before purchasing, using, or charging the batteries.

### Requirements - Software

These software tools may or may not be needed, depending on how you prepare the Pi and where you run the lessons. Check only the devices you plan to use.

1. **Windows PowerShell:** Windows only. It is normally included with Windows; if it is unavailable, follow Microsoft's instructions to install PowerShell before using the Windows commands in this guide.

   **Note:** This is absolutely required on Windows for the commands in this guide.

   **Link:** [PowerShell Installation Guide](https://learn.microsoft.com/en-us/powershell/scripting/install/install-powershell-on-windows)

2. **Terminal:** Included on macOS, Linux, and Raspberry Pi OS; it does not normally need a separate installation. On Windows, **Windows Terminal** is an optional way to open the commands in this guide instead of a standalone PowerShell window. Select its PowerShell profile for Windows commands, and follow Microsoft's setup instructions if you choose to use it.

   **Note:** This is absolutely required on macOS, Linux, and Raspberry Pi OS. For **Windows**, this is **optional**.

   **Link:** [Windows Terminal Installation Guide](https://learn.microsoft.com/en-us/windows/terminal/install)

3. **Raspberry Pi Imager:** Required if your microSD card is new or unflashed. Follow the Raspberry Pi site's installation and setup instructions.

   **Link:** [Raspberry Pi Imager Download](https://www.raspberrypi.com/software/)

4. **Git:** Usually available on macOS, Linux, and Raspberry Pi OS; you may need to install it on Windows. It is needed only if you use `git clone` rather than downloading the ZIP.

   **How to check:** Open **PowerShell** on Windows or **Terminal** on macOS, Linux, or Raspberry Pi OS, then run:

   ```sh
   git --version
   ```

   If the command is unavailable, follow the Git site's instructions to install and set it up.

   **Link:** [Git Download](https://git-scm.com/install/)

5. **Python 3:** Usually available on macOS, Linux, and Raspberry Pi OS; you may need to install it on Windows. The Pi needs it for the lessons, and a separate computer needs it only if it runs lessons.

   **How to check:** Open **PowerShell** on Windows or **Terminal** on macOS, Linux, or Raspberry Pi OS, then run:

   ```powershell
   python --version
   ```

   If that doesn't work, try this:

   ```sh
   python3 --version
   ```

   This repository does not pin a Python version; **Python 3.11** is a conservative choice for a separate computer, while Pi users should keep the version supplied by Raspberry Pi OS. If Python is missing, follow the Python site's installation and setup instructions.

   **Link:** [Python Download](https://www.python.org/downloads/)

6. **VNC Viewer:** Optional, but recommended for comfortable remote control of the Pi's desktop. RealVNC Viewer is one option; follow its site's installation and connection instructions. You can instead use a physical display, keyboard, and mouse, or SSH if you only need a terminal.

   **Link:** [RealVNC Viewer Download](https://www.realvnc.com/en/connect/download/realvnc-viewer/)

### Download

Download the repository on each computer or Raspberry Pi where you plan to run the lessons. Use Git for the steps below, or download a ZIP if you do not want to use Git.

1. Check that Git is available using the instructions in **Requirements - Software** above.
2. Open **PowerShell** on Windows, or **Terminal** on macOS, Linux, or Raspberry Pi OS. Go to the folder where you want to download the project.
3. Run:

   ```sh
   git clone https://github.com/renashall/Smart-Car-Level-3.git
   ```

Alternatively, open the [repository on GitHub](https://github.com/renashall/Smart-Car-Level-3), select **Code**, then **Download ZIP**, and extract it. The extracted folder may have a different name; use its actual name in the commands below.

### Raspberry Pi Setup

Prepare Raspberry Pi OS, then run the car setup scripts on the Pi. These scripts install the system packages needed for the camera, GPIO, and LEDs.

#### Operating System Installation

Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to install **Raspberry Pi OS (64-bit, desktop edition)** for a Pi 3, 4, or 5. Follow [Raspberry Pi's Imager guide](https://www.raspberrypi.com/documentation/computers/getting-started.html) for the installation steps, and keep track of these settings:

- **Hostname:** Set a name for the Pi and save it; you will use it to connect over your local network.
- **Username and Password:** Create a user account and save its credentials for SSH or desktop login.
- **Network:** Configure Wi-Fi if the Pi will not use Ethernet, so it can join the same network as your computer.
- **Enable SSH:** In Imager, turn on SSH and select **Password authentication** for the initial connection.
- **Enable VNC:** Optional but recommended for remote desktop control. The first car setup script enables VNC on the Pi regardless; use it after that script and its reboot.

#### Smart Car Code Installation & Setup

Run these steps on the Pi after it boots. Use the Pi's Terminal directly, or connect from another computer over your local network.

1. If working remotely, connect to the Pi by **SSH** using the hostname and username you saved in Imager, then enter your password when prompted (the password will not appear as you type in Terminal; type it and press Enter when done). Replace `YOUR_USERNAME` and `YOUR_HOSTNAME` with your values:

   ```sh
   ssh YOUR_USERNAME@YOUR_HOSTNAME.local
   ```

   You can use **VNC Viewer** instead if VNC is already enabled: connect to `YOUR_HOSTNAME.local` and sign in with the same username and password. Open Terminal on the Pi after connecting.

   If you have a display and keyboard attached to the Pi, open Terminal there instead.

2. Clone this repository onto the Pi from its Terminal:

   ```sh
   git clone https://github.com/renashall/Smart-Car-Level-3.git
   ```

3. Enter the repository's `Code` folder and make the setup scripts executable:

   ```sh
   cd Smart-Car-Level-3/Code
   chmod +x setupPart1.sh setupPart2.sh
   ```

4. Run the first setup script:

   ```sh
   ./setupPart1.sh
   ```

   It detects your Pi model and OS, enables SSH and VNC on the Pi, installs basic I2C support, and applies the Bullseye patch where needed. Reboot when prompted; afterward, you can connect with VNC Viewer using the Pi's hostname, username, and password.
5. After rebooting, reconnect to the Pi, return to `Code`, and run the second script:

   ```sh
   cd Smart-Car-Level-3/Code
   ./setupPart2.sh
   ```

   It configures the camera, installs the appropriate LED driver and course Python packages, and applies the audio workaround on older Pi models. Reboot again when prompted.

### Computer Setup (Windows, macOS, or Linux)

**Optional:** Use this setup on a Windows, macOS, or Linux laptop or desktop for the camera viewer and GUI lessons (Lessons 6, 7, 8, and 11). Check that Python 3 is available before starting.

1. Open **PowerShell** on Windows or **Terminal** on macOS/Linux. Enter the downloaded project folder:

   ```sh
   cd Smart-Car-Level-3
   ```
2. Run the setup helper with your system Python:

   **Windows PowerShell**

   ```powershell
   python Code\setup.py
   ```

   **macOS/Linux Terminal**

   ```sh
   python3 Code/setup.py
   ```

   The helper creates `.venv` in the project folder and installs the packages in `requirements.txt`. It does not need administrator access or `sudo`. If `.venv` already exists, the helper reuses it; `--force` rebuilds it.
3. Activate the environment and run a lesson. Replace `<PI_IP>` with your Raspberry Pi's IP address, and start the car server on the Pi before running lessons that connect to it.

   **Windows PowerShell**

   ```powershell
   .\.venv\Scripts\Activate.ps1
   python Code\User\lesson_7_face_tracking.py <PI_IP>
   ```

   **macOS/Linux Terminal**

   ```sh
   source .venv/bin/activate
   python3 Code/User/lesson_7_face_tracking.py <PI_IP>
   ```

   If PowerShell blocks activation, run this once and try activating the environment again:

   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
   ```

   When you are finished, leave the environment with:

   ```sh
   deactivate
   ```

### Creating New Code & Testing

Keep your course and experiment scripts in `Code/User` so they stay separate from the Freenove `Code/Server` and `Code/Client` files. The folder also contains example lessons, the shared `car_setup.py` helper, and notes.

1. Create your script in:

   ```text
   Smart-Car-Level-3/Code/User
   ```
2. Import `car_setup` before any car modules. It adds `Code/Server` and `Code/Client` to Python's import path, so you only need it once in each script:

   ```python
   import car_setup

   from Motor import Motor
   from Led import Led
   from Command import COMMAND
   ```
3. On the Raspberry Pi, open **Terminal** in the folder containing the project and run your script:

   ```sh
   cd Smart-Car-Level-3/Code/User
   python3 your_script.py
   ```

---

## Freenove Information

The following sections contain information about Freenove, the original smart car kit maker.

### Support

Contact Freenove for questions about the kit's hardware or original project. Their support covers:

- Quality problems of products
- Problems using the products
- Questions of learning and creation
- Opinions and suggestions
- Ideas and thoughts

Email [support@freenove.com](mailto:support@freenove.com).

### Purchase

Visit [Freenove&#39;s store](http://store.freenove.com) to purchase products. Business customers can email [sale@freenove.com](mailto:sale@freenove.com).

### Copyright

The files in this repository are released under the [Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License](http://creativecommons.org/licenses/by-nc-sa/3.0/). See the license file in this repository for the full terms.

![markdown](https://i.creativecommons.org/l/by-nc-sa/3.0/88x31.png)

You may use the files in derived works under the license terms, but commercial use is not permitted.

Freenove brand and logo are copyright of Freenove Creative Technology Co., Ltd. Can't be used without formal permission.

### About

Freenove is an open-source electronics platform that makes kits, components, and learning materials for electronics projects. Its products and services include:

- Robot kits
- Learning kits for Arduino, Raspberry Pi and micro:bit
- Electronic components and modules, tools
- Product customization service

For more information about Freenove's products and open-source designs, visit [freenove.com](http://www.freenove.com).
