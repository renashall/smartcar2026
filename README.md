## Freenove 4WD Smart Car Kit for Raspberry Pi

> A 4WD smart car kit for Raspberry Pi.

> AI Code Academy has appended this repository for the "Machine Learning with Raspberry Pi Smart Car" course. The original Freenove project files are still present, and the course-specific lesson code lives in `Code/User`.

<img src='Resources/icon.png' width='30%'/>

### Download

- **Use command in console**

  Run following command to download all the files in this repository.

  `git clone https://github.com/Freenove/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi.git`

- **Manually download in browser**

  Click the green "Clone or download" button, then click "Download ZIP" button in the pop-up window.
  Do NOT click the "Open in Desktop" button, it will lead you to install Github software.

> If you meet any difficulties, please contact our support team for help.

### Raspberry Pi Setup

After downloading this repository on your Raspberry Pi, open a terminal in the project folder and run the setup scripts in order.

```sh
cd smartcar2026
chmod +x setupPart1.sh setupPart2.sh
./setupPart1.sh
```

`setupPart1.sh` enables the required Raspberry Pi interfaces, checks the Python command, installs basic I2C support, and applies the Bullseye patch. The script will ask about your Raspberry Pi model and Raspberry Pi OS image date, then prompt you to reboot.

After the Raspberry Pi reboots, return to the project folder and run the second setup script:

```sh
cd smartcar2026
./setupPart2.sh
```

`setupPart2.sh` updates the Raspberry Pi boot configuration for the camera, applies the audio workaround needed by older Raspberry Pi models, installs the car libraries from the `Code` folder, and then prompts you to reboot again.

### Where to Put Your Code

Create your own course and experiment files in:

```text
smartcar2026/Code/User
```

This keeps your work separate from the Freenove `Code/Server` and `Code/Client` files.

When a script in `Code/User` needs to import the car modules, put this line at the top of the script before other car imports:

```python
import car_setup
```

Then import the car code normally. For example:

```python
import car_setup

from Motor import Motor
from Led import Led
from Command import COMMAND
```

`Code/User/car_setup.py` adds the project `Code/Server` and `Code/Client` folders to Python's import path. Keep `car_setup.py` in `Code/User`; you do not need to copy it into each lesson file.

To run one of your scripts from the Raspberry Pi, open a terminal in the `Code/User` folder and run it with Python 3:

```sh
cd smartcar2026/Code/User
python3 your_script.py
```

### Support

Freenove provides free and quick customer support. Including but not limited to:

- Quality problems of products
- Using Problems of products
- Questions of learning and creation
- Opinions and suggestions
- Ideas and thoughts

Please send an email to:

[support@freenove.com](mailto:support@freenove.com)

We will reply to you within one working day.

### Purchase

Please visit the following page to purchase our products:

http://store.freenove.com

Business customers please contact us through the following email address:

[sale@freenove.com](mailto:sale@freenove.com)

### Copyright

All the files in this repository are released under [Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License](http://creativecommons.org/licenses/by-nc-sa/3.0/).

![markdown](https://i.creativecommons.org/l/by-nc-sa/3.0/88x31.png)

This means you can use them on your own derived works, in part or completely. But NOT for the purpose of commercial use.
You can find a copy of the license in this repository.

Freenove brand and logo are copyright of Freenove Creative Technology Co., Ltd. Can't be used without formal permission.

### About

Freenove is an open-source electronics platform.

Freenove is committed to helping customer quickly realize the creative idea and product prototypes, making it easy to get started for enthusiasts of programing and electronics and launching innovative open source products.

Our services include:

- Robot kits
- Learning kits for Arduino, Raspberry Pi and micro:bit
- Electronic components and modules, tools
- Product customization service

Our code and circuit are open source. You can obtain the details and the latest information through visiting the following web site:

http://www.freenove.com
