"""Lesson 6 (viewer side): show the video coming from the Pi camera.

Run this on the Raspberry Pi itself, or on a separate Windows, macOS, or Linux
computer that connects to the Pi over Wi-Fi. First start
lesson_6_pi_camera_stream_server.py on the Raspberry Pi, then run this and pass
the Pi's IP address (use 127.0.0.1 if you run it on the Pi itself), for example:

    python lesson_6_client_video_receiver.py 192.168.1.50

A window opens showing the live camera. Press q in the window to quit.

------------------------------------------------------------------------------
How the network part works
------------------------------------------------------------------------------
This program is the CLIENT. The Pi program is the SERVER. Using the telephone
picture from the server file: the server sits by the phone waiting; this client
DIALS it. A client is simpler than a server - it only needs two steps:
socket() (make the phone) -> connect() (dial the number).

Once connected we read the photos the Pi sends. Remember the Pi's rule
("protocol"): every photo is sent as 4 bytes of LENGTH followed by that many
bytes of JPEG data, and a length of 0 means "the video is over". So to read one
photo we do exactly the reverse of what the Pi does to send it:
  1. read 4 bytes -> turn them into the number N
  2. read exactly N bytes -> that is the whole JPEG
  3. turn those JPEG bytes into a picture we can show
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

    # Make the socket (same AF_INET + SOCK_STREAM / TCP choice as the server,
    # because both ends of a call must speak the same way).
    video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect() dials the server: we must give BOTH the Pi's IP address and the
    # exact port the Pi's server is listening on (8000). This line BLOCKS until
    # the connection succeeds, or raises an error if the Pi isn't reachable or
    # the server isn't running.
    video_socket.connect((pi_ip, VIDEO_PORT))   # dial the Pi's camera port
    # Wrap the socket so we can READ Bytes from it with file-style .read().
    # ("rb" = read, binary.) The server wrapped its end with makefile("wb").
    video_file = video_socket.makefile("rb")
    print("Connected to", pi_ip)


def read_frame():
    """Read one picture from the Pi, or return None when the stream ends.

    This undoes the Pi's length-prefix framing, one photo at a time.
    """
    # Step 1: read the 4 bytes that tell us how big the picture is.
    # video_file.read(4) keeps waiting until it has 4 bytes (or the connection
    # closes). If we get fewer than 4, the Pi hung up, so there is no photo.
    header = video_file.read(4)
    if len(header) != 4:
        return None                        # connection closed before we got them
    # struct.unpack("<L", ...) turns those 4 bytes back into a number. We MUST
    # use the same "<L" the Pi used to pack it (little-endian 4-byte integer),
    # otherwise we would read the size wrong. unpack always hands back a tuple,
    # even for one value, so [0] pulls the single number out of it.
    length = struct.unpack("<L", header)[0]
    if length == 0:
        return None                        # 0 is the Pi's "I'm done" signal

    # Step 2: read exactly that many bytes - the actual JPEG picture. Because
    # TCP is a stream, a single read might not return everything at once on a
    # busy network; reading via makefile keeps pulling until it has `length`
    # bytes. If it still comes up short, the connection broke mid-photo.
    jpeg_data = video_file.read(length)
    if len(jpeg_data) != length:
        return None                        # we got cut off mid-picture

    # Step 3: the bytes are a compressed JPEG. np.frombuffer views them as a row
    # of numbers, and cv2.imdecode unpacks that JPEG into a real picture (a grid
    # of colored pixels) that OpenCV can display.
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
    # Always hang up the phone when done. Closing the file wrapper first, then
    # the socket, frees the network connection so the port isn't left dangling.
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
