"""Lesson 7: Face Detection and Tracking.

You can run this on the Raspberry Pi itself, or on a separate Windows, macOS,
or Linux computer that connects to the Pi over Wi-Fi. Start the smartcar2026
server on the Pi first with `sudo python3 main.py`, then run this with the Pi's
IP address (use 127.0.0.1 if you run it on the Pi itself):

    python lesson_7_face_tracking.py 192.168.1.50

A window shows the camera. When a face is found, the car turns its head to keep
the face in the middle of the picture. Press q to quit.

Face detection is CPU-heavy: a laptop or desktop runs it faster and smoother,
but the Pi works too as long as it has a screen or a VNC desktop.

Lesson 8 imports this file and reuses these functions, so each one is written to
do one clear job (connect, read a picture, find faces, move the head).
"""

import car_setup          # adds the car's code folders to the import path
import socket             # to connect to the Pi over the network
import struct             # to read the 4-byte picture size
import sys                # to read the IP address you type on the command line

import cv2                # OpenCV: shows pictures and finds faces
import numpy as np        # NumPy: turns raw bytes into an image

from command import COMMAND   # the command names the car's server understands

# ---- settings ----
VIDEO_PORT = 8000         # we receive pictures on this port
COMMAND_PORT = 5000       # we send servo commands on this port
FRAME_WIDTH = 400         # picture width in pixels
FRAME_HEIGHT = 300        # picture height in pixels
WINDOW_NAME = "Lesson 7 - Face Tracking"

PAN_SERVO = "0"           # left/right head servo
TILT_SERVO = "1"          # up/down head servo
PAN_MIN, PAN_MAX = 0, 180     # how far the head can turn left/right (degrees)
TILT_MIN, TILT_MAX = 80, 180  # how far the head can tilt up/down (degrees)
SERVO_STEP = 4            # how many degrees to move per step
DEAD_ZONE = 0.15          # ignore tiny offsets so the head does not jitter

# The "cascade" is a file that teaches OpenCV what a face looks like.
# car_setup.CODE_DIR points at the Code folder, so we can find it reliably.
CASCADE_PATH = car_setup.CODE_DIR / "Client" / "haarcascade_frontalface_default.xml"

# ---- things created in setup ----
cmd = None                # holds command names like cmd.CMD_SERVO
face_cascade = None       # the face detector
video_socket = None       # connection that receives pictures
video_file = None         # that connection, read like a file
command_socket = None     # connection that sends servo commands
pan_angle = 90.0          # current left/right head angle (90 = straight ahead)
tilt_angle = 90.0         # current up/down head angle


def setup():
    """Connect to the Pi and get the face detector ready."""
    global cmd, face_cascade, video_socket, video_file, command_socket

    # The IP address is the first thing you type after the file name.
    if len(sys.argv) < 2:
        raise SystemExit("Please pass the Pi's IP address, e.g. python this.py 192.168.1.50")

    cmd = COMMAND()
    # Load the face detector from the cascade file.
    face_cascade = cv2.CascadeClassifier(str(CASCADE_PATH))
    if face_cascade.empty():              # empty() is True if the file failed to load
        raise FileNotFoundError("Could not load the face file: " + str(CASCADE_PATH))

    pi_ip = sys.argv[1]
    # Open the picture connection (port 8000) and read it like a file.
    video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    video_socket.connect((pi_ip, VIDEO_PORT))
    video_file = video_socket.makefile("rb")

    # Open a second connection (port 5000) for sending servo commands.
    command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    command_socket.connect((pi_ip, COMMAND_PORT))
    print("Connected to", pi_ip)


def read_frame():
    """Read one picture from the Pi, or return None when the stream ends."""
    header = video_file.read(4)           # first 4 bytes = the picture's size
    if len(header) != 4:
        return None
    length = struct.unpack("<L", header)[0]   # turn those bytes into a number
    if length == 0:
        return None
    jpeg_data = video_file.read(length)   # read exactly that many bytes
    if len(jpeg_data) != length:
        return None
    # Turn the raw JPEG bytes into a picture we can search and show.
    return cv2.imdecode(np.frombuffer(jpeg_data, dtype=np.uint8), cv2.IMREAD_COLOR)


def detect_faces(frame):
    """Return a list of (x, y, w, h) boxes, one for each face found."""
    # Face detection works on a grey (black-and-white) version of the picture.
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # detectMultiScale scans the picture and returns a box for each face.
    # 1.3 and 5 control how carefully it searches.
    return face_cascade.detectMultiScale(gray, 1.3, 5)


def biggest_face(faces):
    """Return the (x, y, w, h) of the largest face, or None if there are none."""
    if len(faces) == 0:
        return None
    # The nearest face is usually the biggest. Each box is (x, y, w, h), so
    # face[2] * face[3] is width * height = the box's area.
    return max(faces, key=lambda face: face[2] * face[3])


def send_servo(channel, angle):
    """Send one servo command to the car, e.g. CMD_SERVO#0#95."""
    # The server expects: command name, then "#", then values, then a newline.
    message = cmd.CMD_SERVO + "#" + channel + "#" + str(int(angle)) + "\n"
    command_socket.send(message.encode("utf-8"))   # text must be sent as bytes


def track_face(face):
    """Turn the head a little so the given face moves toward the middle."""
    global pan_angle, tilt_angle
    if face is None:
        return                            # nothing to follow
    x, y, w, h = face
    center_x = x + w / 2                  # middle of the face, left-to-right
    center_y = y + h / 2                  # middle of the face, top-to-bottom
    # offset is -1 at the left/top edge, +1 at the right/bottom edge, 0 in the middle.
    offset_x = (center_x / FRAME_WIDTH - 0.5) * 2
    offset_y = (center_y / FRAME_HEIGHT - 0.5) * 2
    # If the face is already near the centre, don't move (stops the jitter).
    if abs(offset_x) < DEAD_ZONE and abs(offset_y) < DEAD_ZONE:
        return
    # Nudge the head toward the face, but never past the servo's limits.
    pan_angle = clamp(pan_angle + SERVO_STEP * offset_x, PAN_MIN, PAN_MAX)
    tilt_angle = clamp(tilt_angle - SERVO_STEP * offset_y, TILT_MIN, TILT_MAX)
    send_servo(PAN_SERVO, pan_angle)
    send_servo(TILT_SERVO, tilt_angle)


def clamp(value, low, high):
    """Keep a number between low and high (never smaller, never bigger)."""
    return max(low, min(high, value))


def loop():
    """Read pictures, find the biggest face, follow it, and show the video."""
    while True:
        frame = read_frame()
        if frame is None:
            break
        face = biggest_face(detect_faces(frame))   # find the closest face
        if face is not None:
            x, y, w, h = face
            # Draw a green box around the face we are tracking.
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            track_face(face)                        # turn the head toward it
        cv2.imshow(WINDOW_NAME, frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):       # press q to quit
            break


def destroy():
    """Close both connections and the window when we are finished."""
    if video_file is not None:
        video_file.close()
    if video_socket is not None:
        video_socket.close()
    if command_socket is not None:
        command_socket.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        pass
    finally:
        destroy()
