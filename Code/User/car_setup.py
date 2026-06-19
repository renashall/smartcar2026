"""Helper so your lesson scripts can use the car's code.

Put your lesson scripts in this same folder (smartcar2026/Code/User) and start
each script with this single line BEFORE you import any car module:

    import car_setup

After that, you can import the car's modules normally, for example:

    from motor import Motor
    from led import Led
    from command import COMMAND

How it works: this file finds the folder it lives in, steps up to the "Code"
folder, and adds the Server and Client folders to Python's import path. That
means you never have to write long file paths yourself.
"""

# "sys" lets us look at and change Python's settings while the program runs.
# We use it here to add folders to the list of places Python searches for code.
import sys

# "Path" is a friendly way to work with file and folder locations.
from pathlib import Path

# __file__ is the location of THIS file (car_setup.py).
#   .resolve()      turns it into a full, exact path (no shortcuts like "..").
#   .parent         is the folder this file is in  -> .../Code/User
#   .parent.parent  goes up one more level         -> .../Code
# So CODE_DIR always points at the car's "Code" folder, no matter which
# computer the project is copied onto.
CODE_DIR = Path(__file__).resolve().parent.parent   # .../smartcar2026/Code

# The car's code is split across these folders. We add each one to Python's
# search path so that "from motor import Motor" (and friends) just work.
for folder_name in ("Server", "Client"):
    folder = CODE_DIR / folder_name          # build the full path to the folder

    # Only add a folder if it really exists, and don't add it twice.
    if folder.is_dir() and str(folder) not in sys.path:
        # sys.path is the list of folders Python searches when you "import"
        # something. insert(0, ...) puts our folder at the FRONT of that list,
        # so the car's modules are found first.
        sys.path.insert(0, str(folder))
