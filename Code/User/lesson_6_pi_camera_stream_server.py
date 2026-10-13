"""Lesson 6 (Raspberry Pi side): stream the camera to the computer.

Run this on the Raspberry Pi (the car).
It opens the camera, waits for the computer program to connect, and then sends
one JPEG picture after another. Each picture is sent as: 4 bytes that say how
big the picture is, then the picture data itself. The computer side
(lesson_6_client_video_receiver.py) reads them back the same way.

------------------------------------------------------------------------------
How the network part works (read this first!)
------------------------------------------------------------------------------
Two programs on two different machines talk to each other through a "socket".
Think of a socket as the two ends of a telephone call:

  * This program (on the Pi) is the SERVER. A server waits by the phone for
    someone to call. The steps are always: socket() -> bind() -> listen() ->
    accept(). After accept() the call is connected and we can talk.
  * The other program (on your computer) is the CLIENT. It dials our number
    with connect(). See lesson_6_client_video_receiver.py.

We use TCP (SOCK_STREAM). TCP is reliable: every byte you send arrives, in the
same order, with nothing missing. That sounds perfect, but it has one catch:

  TCP is a STREAM of bytes, not a stack of separate messages. If we send three
  photos in a row, the other side just sees one long river of bytes. It has no
  built-in way to know where one photo ends and the next begins.

So WE invent the rule (a "protocol"): before each photo we send its length as a
fixed 4-byte number. The receiver reads exactly 4 bytes, learns the size N,
then reads exactly N more bytes to get the whole photo. This trick is called
"length-prefix framing". A length of 0 is our special "no more photos" signal.
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
    """Open the network doorway and start the camera.

    This runs the first three steps of every TCP server:
    socket() (make the phone) -> bind() (claim our number) -> listen()
    (turn the ringer on). The fourth step, accept(), happens in accept_client().
    """
    global server_socket, camera

    # socket() makes the "phone" but does not connect it to anyone yet.
    #   AF_INET    = use ordinary IPv4 internet addresses (like 192.168.1.50).
    #   SOCK_STREAM = use TCP: a reliable, in-order connection. (The other
    #                 common choice, SOCK_DGRAM/UDP, is faster but can lose or
    #                 reorder data - bad for a picture, so we avoid it.)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # SO_REUSEADDR lets us grab the same port number again immediately after
    # the program restarts. Without it the operating system keeps the old port
    # "busy" for a minute or two and bind() below would fail with
    # "Address already in use".
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind() claims an address (which network card) and a port (which "door
    # number") on this machine. HOST = "" means "any of our network cards", so
    # the client can reach us over Wi-Fi, Ethernet, or even from the Pi itself.
    server_socket.bind((HOST, VIDEO_PORT))   # claim the port number
    # listen() flips the socket into "waiting for callers" mode. The 1 is the
    # backlog: how many callers may wait in line while we are busy. We only
    # serve one viewer, so 1 is plenty.
    server_socket.listen(1)                  # start listening for 1 connection
    print("Camera server is ready on port", VIDEO_PORT, "- waiting for the computer...")

    camera = Picamera2()
    camera.configure(camera.create_video_configuration(
        main={"size": (FRAME_WIDTH, FRAME_HEIGHT)}))
    camera.start()
    time.sleep(WARMUP_SECONDS)               # let the camera settle


def accept_client():
    """Wait here until the computer program connects, then open the pipe.

    This is step four of the server: accept(). It is the moment the phone call
    actually connects.
    """
    global connection
    # accept() BLOCKS (pauses the whole program) until a client calls in. When
    # one does, it returns TWO things:
    #   client_socket - a brand-new socket dedicated to THIS one caller. (The
    #                   original server_socket keeps listening for future
    #                   callers; we talk to the client through client_socket.)
    #   address       - the caller's (IP address, port), so we can see who it is.
    client_socket, address = server_socket.accept()
    # A socket sends/receives raw bytes. makefile("wb") wraps it so we can WRITE
    # Bytes to it using simple file-style .write()/.flush() calls. ("wb" = write,
    # binary.) The client wraps its end with makefile("rb") to read.
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

        # --- This is the "length-prefix framing" described at the top. ---
        # First send the SIZE of this picture so the computer knows exactly how
        # many bytes to read next. struct.pack turns a Python number into raw
        # bytes:
        #   "<L" means  <  = little-endian (least-significant byte first) and
        #               L  = an unsigned 4-byte integer (0 .. 4,294,967,295).
        # Both sides MUST agree on "<L" or the size would be misread. 4 bytes is
        # always 4 bytes, so the receiver can confidently read exactly 4.
        length = stream.tell()               # how many bytes the photo took
        connection.write(struct.pack("<L", length))
        connection.flush()                   # push it out now, don't wait

        # Now send the picture data itself: exactly `length` bytes.
        stream.seek(0)                       # rewind to the start of the photo
        connection.write(stream.read())


def destroy():
    """Tell the computer we are done and close everything tidily."""
    if connection is not None:
        try:
            # Send one last length of 0. The receiver's rule is "length 0 means
            # the video is over", so this politely tells it to stop instead of
            # leaving it waiting forever for a photo that never comes.
            connection.write(struct.pack("<L", 0))
        except OSError:
            pass                             # the computer may already be gone
        # close() hangs up our end of the call and frees the network resources.
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
