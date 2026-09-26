"""Lesson 11: Camera GUI (Bonus).

Run this on the Raspberry Pi itself, or on a separate Windows, macOS, or Linux
computer that connects to the Pi over Wi-Fi, while the Raspberry Pi runs the
Smart-Car-Level-3 server (`sudo python3 main.py`). Type the Pi's IP address into the
box (use 127.0.0.1 if you run it on the Pi itself).

The window shows the live camera, lets you move the head with buttons and
sliders, and has a checkbox to turn face tracking on and off.

Note: a graphical window (PyQt5) needs one "window class". That is the only
class in this file - everything else is plain functions, like the other lessons.
"""

import car_setup          # adds the car's code folders to the import path
import socket             # to talk to the Pi over the network
import struct             # to read the 4-byte picture size
import sys
import threading          # to receive video in the background

import cv2                # OpenCV: decodes pictures and finds faces
import numpy as np        # NumPy: turns raw bytes into an image
# PyQt5 is the toolkit that builds the window, buttons, and sliders.
from PyQt5 import QtCore, QtGui, QtWidgets

from command import COMMAND   # the command names the car's server understands

# ---- settings ----
VIDEO_PORT = 8000             # we receive pictures on this port
COMMAND_PORT = 5000           # we send servo commands on this port
FRAME_WIDTH = 400
FRAME_HEIGHT = 300
PAN_SERVO = "0"               # left/right head servo
TILT_SERVO = "1"              # up/down head servo
PAN_MIN, PAN_MAX = 0, 180
TILT_MIN, TILT_MAX = 80, 180
SERVO_STEP = 4                # degrees moved per face-tracking step
DEAD_ZONE = 0.15             # ignore tiny offsets so the head does not jitter
CASCADE_PATH = car_setup.CODE_DIR / "Client" / "haarcascade_frontalface_default.xml"

# ---- shared state used by the background video thread ----
# These are "global" because both the background thread and the window need
# to use them.
cmd = COMMAND()                          # command names like cmd.CMD_SERVO
face_cascade = cv2.CascadeClassifier(str(CASCADE_PATH))   # the face detector
video_socket = None                      # connection that receives pictures
video_file = None                        # that connection, read like a file
command_socket = None                    # connection that sends servo commands
latest_frame = None                      # the most recent picture, ready to show
frame_lock = threading.Lock()            # keeps the picture safe to share between threads
running = False                          # True while the video thread should run
track_faces = False                      # True when the "Track faces" box is ticked
pan_angle = 90.0                         # current left/right head angle
tilt_angle = 90.0                        # current up/down head angle


def connect(pi_ip):
    """Open the video and command connections to the Pi."""
    global video_socket, video_file, command_socket
    # Connection 1: pictures come in on port 8000.
    video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    video_socket.connect((pi_ip, VIDEO_PORT))
    video_file = video_socket.makefile("rb")
    # Connection 2: servo commands go out on port 5000.
    command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    command_socket.connect((pi_ip, COMMAND_PORT))


def read_frame():
    """Read one picture from the Pi, or return None when the stream ends."""
    header = video_file.read(4)              # first 4 bytes = the picture's size
    if len(header) != 4:
        return None
    length = struct.unpack("<L", header)[0]  # turn those bytes into a number
    if length == 0:
        return None
    jpeg_data = video_file.read(length)      # read exactly that many bytes
    if len(jpeg_data) != length:
        return None
    return cv2.imdecode(np.frombuffer(jpeg_data, dtype=np.uint8), cv2.IMREAD_COLOR)


def send_servo(channel, angle):
    """Send one servo command to the car, e.g. CMD_SERVO#0#95."""
    if command_socket is None:
        return                               # not connected yet, so do nothing
    message = cmd.CMD_SERVO + "#" + channel + "#" + str(int(angle)) + "\n"
    command_socket.send(message.encode("utf-8"))


def clamp(value, low, high):
    """Keep a number between low and high."""
    return max(low, min(high, value))


def track_face(face):
    """Turn the head a little so the given face moves toward the middle."""
    global pan_angle, tilt_angle
    x, y, w, h = face
    # offset is -1 at the left/top edge, +1 at the right/bottom edge, 0 in the middle.
    offset_x = ((x + w / 2) / FRAME_WIDTH - 0.5) * 2
    offset_y = ((y + h / 2) / FRAME_HEIGHT - 0.5) * 2
    if abs(offset_x) < DEAD_ZONE and abs(offset_y) < DEAD_ZONE:
        return                               # already centred: don't move
    pan_angle = clamp(pan_angle + SERVO_STEP * offset_x, PAN_MIN, PAN_MAX)
    tilt_angle = clamp(tilt_angle - SERVO_STEP * offset_y, TILT_MIN, TILT_MAX)
    send_servo(PAN_SERVO, pan_angle)
    send_servo(TILT_SERVO, tilt_angle)


def video_thread():
    """Runs in the background: read pictures, optionally find a face, store it.

    Reading pictures is slow, so we do it in a separate thread. That keeps the
    window responsive (buttons still click) while video keeps flowing.
    """
    global latest_frame
    while running:
        frame = read_frame()
        if frame is None:
            break
        # If face tracking is switched on, find faces and follow the biggest.
        if track_faces:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            if len(faces) > 0:
                # max(..., key=area) picks the biggest box (width * height).
                track_face(max(faces, key=lambda f: f[2] * f[3]))
        # Hand the finished picture to the window. The lock makes sure the
        # window never reads the picture while we are halfway through saving it.
        with frame_lock:
            latest_frame = frame


class CameraWindow(QtWidgets.QMainWindow):
    """The single window: video on the left, controls on the right."""

    def __init__(self):
        # Let PyQt set up the basic window first.
        super().__init__()
        self.setWindowTitle("Lesson 11 - Camera GUI (Bonus)")

        # The label that the video picture is drawn onto.
        self.video_label = QtWidgets.QLabel("Not connected")
        self.video_label.setFixedSize(FRAME_WIDTH, FRAME_HEIGHT)
        self.video_label.setAlignment(QtCore.Qt.AlignCenter)

        # A text box for the Pi's IP address and a button to connect.
        self.ip_box = QtWidgets.QLineEdit("192.168.1.50")
        connect_button = QtWidgets.QPushButton("Connect")
        connect_button.clicked.connect(self.on_connect)   # run on_connect when clicked

        # A tick box to turn face tracking on and off.
        self.track_checkbox = QtWidgets.QCheckBox("Track faces")
        self.track_checkbox.stateChanged.connect(self.on_track_changed)

        # Five buttons to move the head by hand.
        up = QtWidgets.QPushButton("Up")
        down = QtWidgets.QPushButton("Down")
        left = QtWidgets.QPushButton("Left")
        right = QtWidgets.QPushButton("Right")
        home = QtWidgets.QPushButton("Home")
        # Each button calls nudge() with which servo to move and by how much.
        # (lambda is a tiny throwaway function used to pass those values along.)
        up.clicked.connect(lambda: self.nudge(TILT_SERVO, +SERVO_STEP))
        down.clicked.connect(lambda: self.nudge(TILT_SERVO, -SERVO_STEP))
        left.clicked.connect(lambda: self.nudge(PAN_SERVO, -SERVO_STEP))
        right.clicked.connect(lambda: self.nudge(PAN_SERVO, +SERVO_STEP))
        home.clicked.connect(self.go_home)

        # Arrange the five buttons in a little plus-sign grid:
        #        Up
        #   Left Home Right
        #       Down
        pad = QtWidgets.QGridLayout()
        pad.addWidget(up, 0, 1)
        pad.addWidget(left, 1, 0)
        pad.addWidget(home, 1, 1)
        pad.addWidget(right, 1, 2)
        pad.addWidget(down, 2, 1)

        # Stack the controls down the right-hand side.
        controls = QtWidgets.QVBoxLayout()
        controls.addWidget(self.ip_box)
        controls.addWidget(connect_button)
        controls.addWidget(self.track_checkbox)
        controls.addLayout(pad)
        controls.addStretch(1)               # push everything up to the top

        # Put the video on the left and the controls on the right.
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.video_label)
        layout.addLayout(controls)
        container = QtWidgets.QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # A timer pulls the newest picture onto the screen about 33 times a
        # second (every 30 milliseconds), so the video looks smooth.
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh_video)
        self.timer.start(30)

    def on_connect(self):
        """Connect to the Pi and start the background video thread."""
        global running
        try:
            connect(self.ip_box.text())      # use whatever IP is in the text box
        except OSError as error:
            self.video_label.setText("Could not connect:\n" + str(error))
            return
        running = True
        thread = threading.Thread(target=video_thread)
        thread.daemon = True                 # let it stop when the app closes
        thread.start()

    def on_track_changed(self):
        """Remember whether the 'Track faces' box is ticked."""
        global track_faces
        track_faces = self.track_checkbox.isChecked()

    def nudge(self, channel, change):
        """Move one servo a few degrees when an arrow button is pressed."""
        global pan_angle, tilt_angle
        if channel == PAN_SERVO:
            pan_angle = clamp(pan_angle + change, PAN_MIN, PAN_MAX)
            send_servo(PAN_SERVO, pan_angle)
        else:
            tilt_angle = clamp(tilt_angle + change, TILT_MIN, TILT_MAX)
            send_servo(TILT_SERVO, tilt_angle)

    def go_home(self):
        """Recentre the head to look straight ahead."""
        global pan_angle, tilt_angle
        pan_angle, tilt_angle = 90.0, 90.0
        send_servo(PAN_SERVO, pan_angle)
        send_servo(TILT_SERVO, tilt_angle)

    def refresh_video(self):
        """Copy the newest picture from the thread and draw it in the window."""
        # Take a quick copy under the lock so the thread can keep working.
        with frame_lock:
            frame = None if latest_frame is None else latest_frame.copy()
        if frame is None:
            return                           # no picture yet
        # OpenCV uses Blue-Green-Red order, but Qt expects Red-Green-Blue, so swap.
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, _ = rgb.shape
        # Wrap the raw pixels in a Qt image, then show it on the label.
        image = QtGui.QImage(rgb.data, width, height, 3 * width, QtGui.QImage.Format_RGB888)
        self.video_label.setPixmap(QtGui.QPixmap.fromImage(image))


def destroy():
    """Stop the thread and close the connections when the app ends."""
    global running
    running = False                          # tell the video thread to stop
    if video_file is not None:
        video_file.close()
    if video_socket is not None:
        video_socket.close()
    if command_socket is not None:
        command_socket.close()


if __name__ == "__main__":
    # Every PyQt program needs one QApplication. It runs the window and watches
    # for clicks and key presses.
    app = QtWidgets.QApplication(sys.argv)
    window = CameraWindow()
    window.show()
    try:
        app.exec_()                          # this line runs until you close the window
    finally:
        destroy()                            # always clean up on the way out
