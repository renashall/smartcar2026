# Code/User Folder

This folder is for AI Code Academy lesson files and your own smart car programs.

Use `Code/User` when you are writing new code for the course, testing an idea, or saving a finished lesson script. Keeping your files here prevents course work from being mixed into the original Freenove `Code/Server`, `Code/Client`, and `Code/Modules` folders.

## Using `car_setup.py`

Most lesson scripts in this folder should start with:

```python
import car_setup
```

That line lets your script import the smart car modules without writing long file paths. Put it before imports such as:

```python
from Motor import Motor
from Led import Led
from ADC import Adc
```

`car_setup.py` must stay in this folder. You only import it from your script; you do not need to edit it for normal lessons.

## Running Your Code

From the Raspberry Pi terminal:

```sh
cd smartcar2026/Code/User
python3 lesson_1_components.py
```

Replace `lesson_1_components.py` with the file you want to run.
