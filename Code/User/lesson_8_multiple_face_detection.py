"""Lesson 8: Multiple Face Detection.

You can run this on the Raspberry Pi itself, or on a separate Windows, macOS, or
Linux computer that connects to the Pi over Wi-Fi. Start the Smart-Car-Level-3 server
on the Pi first with `sudo python3 main.py`, then run (use 127.0.0.1 as the
address if you run it on the Pi itself):

    python lesson_8_multiple_face_detection.py 192.168.1.50

Lesson 7 already knows how to connect to the Pi, read a picture, find faces, and
turn the head. This lesson IMPORTS Lesson 7 and reuses all of that, then adds a
new multi-face idea: target lock. The first target is the biggest face, but after
that the program tries to keep following the face nearest to the previous target.
This makes tracking less jumpy when two people are in view.

(Importing Lesson 7 also runs its `import car_setup`, so the car's code folders
are ready for us too. Keep this file in the same folder as Lesson 7.)

------------------------------------------------------------------------------
How the network part works
------------------------------------------------------------------------------
There is no new networking code in this lesson - it all comes from Lesson 7,
which we imported as `face`. When we call:

  * face.setup()       -> opens the two TCP connections (video on port 8000,
                          commands on port 5000) and loads the face detector.
  * face.read_frame()  -> reads one photo using the 4-byte-length framing.
  * face.track_face()  -> sends servo commands over the command connection.
  * face.destroy()     -> closes both connections at the end.

So the whole video-in / commands-out pipeline is identical to Lesson 7. The ONLY
new thing here is smarter logic for picking WHICH face to follow when several
are on screen (see choose_target below).

Press q to quit.
"""

import cv2                # OpenCV: we use it here just to draw on the picture

# Import all of Lesson 7's functions. "as face" gives them a short nickname,
# so we can write face.read_frame(), face.detect_faces(), and so on.
# Importing a file runs its top part (imports, settings, function definitions)
# but NOT its "if __name__ == '__main__'" block, so Lesson 7 does not start
# running on its own here.
import lesson_7_face_tracking as face

WINDOW_NAME = "Lesson 8 - Multiple Face Detection"
BOX_COLOR = (0, 255, 0)          # green
TARGET_COLOR = (0, 255, 255)    # yellow
LOCK_DISTANCE = 85               # pixels: how far the target can move and stay locked


def face_center(face_box):
    """Return the middle point of a face box."""
    x, y, w, h = face_box
    return int(x + w / 2), int(y + h / 2)


def center_distance(first_face, second_face):
    """Return the distance between two face centers."""
    first_x, first_y = face_center(first_face)
    second_x, second_y = face_center(second_face)
    return ((first_x - second_x) ** 2 + (first_y - second_y) ** 2) ** 0.5


def choose_target(faces, previous_target):
    """Choose one face to follow, using the previous target when possible."""
    if len(faces) == 0:
        return None, "none"

    # When there is no previous target, start with the biggest face. The biggest
    # face is usually the closest person.
    if previous_target is None:
        return face.biggest_face(faces), "largest"

    # After we have a target, choose the new box closest to where that target was
    # in the last frame. This gives the program a simple memory.
    closest_face = min(faces, key=lambda face_box: center_distance(face_box, previous_target))
    if center_distance(closest_face, previous_target) <= LOCK_DISTANCE:
        return closest_face, "locked"

    # If no detected face is close enough, start over with the biggest face.
    return face.biggest_face(faces), "largest"


def draw_faces(frame, faces, target, target_mode):
    """Draw every face and highlight the target face."""
    for face_box in faces:
        x, y, w, h = face_box
        cv2.rectangle(frame, (x, y), (x + w, y + h), BOX_COLOR, 2)

    # The target is the one face the car follows. It may be the largest face, or
    # it may be the face closest to the previous target.
    if target is not None:
        x, y, w, h = target
        center = face_center(target)     # middle point of the face
        cv2.circle(frame, center, int((w + h) / 4), TARGET_COLOR, 2)
        cv2.putText(frame, "target: " + target_mode,
                    (x, min(frame.shape[0] - 10, y + h + 18)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, TARGET_COLOR, 1, cv2.LINE_AA)


def draw_detection_summary(frame, faces, target, target_mode):
    """Show a short summary for this video frame."""
    if target is None:
        summary = "faces: 0  target: none"
    else:
        summary = "faces: " + str(len(faces)) + "  target: " + target_mode
    cv2.putText(frame, summary, (10, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, TARGET_COLOR, 2, cv2.LINE_AA)


def loop():
    """Read pictures, mark all faces, keep a target lock, and show the video."""
    previous_target = None
    while True:
        # face.read_frame() pulls one photo off the VIDEO connection (port 8000)
        # using Lesson 7's code. It returns None when the Pi ends the stream.
        frame = face.read_frame()           # from Lesson 7: get one picture
        if frame is None:
            break
        faces = face.detect_faces(frame)    # from Lesson 7: find EVERY face
        target, target_mode = choose_target(faces, previous_target)
        previous_target = target
        draw_faces(frame, faces, target, target_mode)
        draw_detection_summary(frame, faces, target, target_mode)
        # face.track_face() sends servo commands over the COMMAND connection
        # (port 5000), again using Lesson 7's code, to steer the head.
        face.track_face(target)             # from Lesson 7: turn toward the target
        cv2.imshow(WINDOW_NAME, frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


if __name__ == "__main__":
    try:
        face.setup()        # from Lesson 7: connect + load the face detector
        loop()
    except KeyboardInterrupt:
        pass
    finally:
        face.destroy()      # from Lesson 7: close the sockets and window
