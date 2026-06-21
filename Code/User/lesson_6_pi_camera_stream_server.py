"""Lesson 6 (Raspberry Pi side): stream the camera to the computer.

Run this on the Raspberry Pi (the car).
It opens the camera, waits for the computer program to connect, and then sends
one JPEG picture after another. Each picture is sent as: 4 bytes that say how
big the picture is, then the picture data itself. The computer side
(lesson_6_client_video_receiver.py) reads them back the same way.
"""

import io                 # io.BytesIO gives us an in-memory "file" for the photo
import socket             # socket lets two computers talk over the network
import struct             # struct turns a number into a fixed set of bytes
import time

from picamera2 import Picamera2   # controls the Raspberry Pi camera (Bookworm)

# ---- settings ----
VIDEO_PORT = 8000         # the "door number" the computer connects to
HOST = ""                 # "" means "accept a connection on any of our addresses"
FRAME_WIDTH = 400         # picture width in pixels
FRAME_HEIGHT = 300        # picture height in pixels
FRAME_RATE = 15           # how many pictures per second to capture
WARMUP_SECONDS = 2        # give the camera a moment to adjust before streaming

# ---- things created in setup ----
server_socket = None      # the "doorway" that waits for the computer
connection = None         # the open pipe we write pictures into
camera = None


def setup():
    """Open the network doorway and start the camera."""
    global server_socket, camera

    # AF_INET = use normal internet addresses; SOCK_STREAM = a reliable, ordered
    # connection (TCP). This is the same kind of connection web pages use.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # This option lets us reuse the port right away if we restart the program.
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, VIDEO_PORT))   # claim the port number
    server_socket.listen(1)                  # start listening for 1 connection
    print("Camera server is ready on port", VIDEO_PORT, "- waiting for the computer...")

    camera = Picamera2()
    camera.configure(camera.create_video_configuration(
        main={"size": (FRAME_WIDTH, FRAME_HEIGHT)}))
    camera.start()
    time.sleep(WARMUP_SECONDS)               # let the camera settle


def accept_client():
    """Wait here until the computer program connects, then open the pipe."""
    global connection
    # accept() pauses the program until someone connects. It hands back the new
    # connection and the address of whoever connected.
    client_socket, address = server_socket.accept()
    # makefile("wb") lets us WRITE Bytes to the connection like writing to a file.
    connection = client_socket.makefile("wb")
    print("Computer connected from", address[0])


def loop():
    """Capture pictures forever and send each one down the pipe."""
    stream = io.BytesIO()                     # an empty in-memory file for the photo
    while True:
        # Empty the in-memory file, then take one fresh JPEG photo into it.
        stream.seek(0)
        stream.truncate()
        camera.capture_file(stream, format="jpeg")

        # First send the SIZE of this picture so the computer knows how many
        # bytes to read. struct.pack("<L", length) makes a 4-byte number.
        length = stream.tell()               # how many bytes the photo took
        connection.write(struct.pack("<L", length))
        connection.flush()                   # push it out now, don't wait

        # Now send the picture data itself.
        stream.seek(0)                       # rewind to the start of the photo
        connection.write(stream.read())


def destroy():
    """Tell the computer we are done and close everything tidily."""
    if connection is not None:
        try:
            # A length of 0 is our agreed signal for "no more pictures, stop".
            connection.write(struct.pack("<L", 0))
        except OSError:
            pass                             # the computer may already be gone
        connection.close()
    if camera is not None:
        camera.stop()
        camera.close()
    if server_socket is not None:
        server_socket.close()


if __name__ == "__main__":
    try:
        setup()
        accept_client()                      # wait for the computer to connect
        loop()                               # then stream pictures
    except KeyboardInterrupt:
        pass
    finally:
        destroy()
