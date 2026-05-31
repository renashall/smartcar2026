"""Lesson 6 (computer side): show the video coming from the Pi camera.

Run this on your Windows or macOS computer.
First start lesson_6_pi_camera_stream_server.py on the Raspberry Pi, then run
this and pass the Pi's IP address, for example:

    python lesson_6_client_video_receiver.py 192.168.1.50

A window opens showing the live camera. Press q in the window to quit.
"""

import socket             # to connect to the Pi over the network
import struct             # to turn the 4 size-bytes back into a number
import sys                # sys.argv lets us read the IP address you type in

import cv2                # OpenCV: shows the picture in a window
import numpy as np        # NumPy: helps turn raw bytes into an image

# ---- settings ----
VIDEO_PORT = 8000                          # must match the Pi server's port
WINDOW_NAME = "Lesson 6 - Pi Camera"       # the title of the video window

# ---- things created in setup ----
video_socket = None       # our connection to the Pi
video_file = None         # the same connection, read like a file


def setup():
    """Read the Pi's address from the command line and connect to it."""
    global video_socket, video_file

    # When you run "python thisfile.py 192.168.1.50", sys.argv[1] is the IP.
    # If you forget to type it, stop with a friendly reminder.
    if len(sys.argv) < 2:
        raise SystemExit("Please pass the Pi's IP address, e.g. python this.py 192.168.1.50")
    pi_ip = sys.argv[1]

    video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    video_socket.connect((pi_ip, VIDEO_PORT))   # dial the Pi's camera port
    # makefile("rb") lets us READ Bytes from the connection like a file.
    video_file = video_socket.makefile("rb")
    print("Connected to", pi_ip)


def read_frame():
    """Read one picture from the Pi, or return None when the stream ends."""
    # Step 1: read the 4 bytes that tell us how big the picture is.
    header = video_file.read(4)
    if len(header) != 4:
        return None                        # connection closed before we got them
    # struct.unpack("<L", ...) turns those 4 bytes back into a number.
    # The [0] is because unpack always hands back a tuple, even of one item.
    length = struct.unpack("<L", header)[0]
    if length == 0:
        return None                        # 0 is the Pi's "I'm done" signal

    # Step 2: read exactly that many bytes - the actual JPEG picture.
    jpeg_data = video_file.read(length)
    if len(jpeg_data) != length:
        return None                        # we got cut off mid-picture

    # Step 3: turn the raw JPEG bytes into a picture OpenCV can show.
    return cv2.imdecode(np.frombuffer(jpeg_data, dtype=np.uint8), cv2.IMREAD_COLOR)


def loop():
    """Keep reading pictures and showing them until the video ends or you quit."""
    while True:
        frame = read_frame()
        if frame is None:
            break                          # no more pictures: leave the loop
        cv2.imshow(WINDOW_NAME, frame)     # draw the picture in the window
        # waitKey(1) waits 1 millisecond for a key press and lets the window
        # refresh. If that key was "q", we stop.
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


def destroy():
    """Close the connection and the window when we are finished."""
    if video_file is not None:
        video_file.close()
    if video_socket is not None:
        video_socket.close()
    cv2.destroyAllWindows()                # close any OpenCV windows


if __name__ == "__main__":
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        pass
    finally:
        destroy()
