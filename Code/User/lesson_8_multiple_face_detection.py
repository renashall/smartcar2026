"""Lesson 8: Multiple Face Detection.

Run this on your Windows or macOS computer. Start the smartcar2026 server on the
Pi first with `sudo python3 main.py`, then run:

    python lesson_8_multiple_face_detection.py 192.168.1.50

Lesson 7 already knows how to connect to the Pi, read a picture, find faces, and
turn the head. This lesson IMPORTS Lesson 7 and reuses all of that, then adds one
new idea: instead of only the biggest face, draw a box around EVERY face and put
a yellow circle around the biggest one (the "target" the head follows).

(Importing Lesson 7 also runs its `import car_setup`, so the car's code folders
are ready for us too. Keep this file in the same folder as Lesson 7.)

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


def draw_faces(frame, faces, target):
    """Draw a green box on every face and a yellow circle on the biggest one."""
    # Loop over every face the detector found and draw a green box around it.
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # The "target" is the biggest face. If we found one, highlight it.
    if target is not None:
        x, y, w, h = target
        center = (int(x + w / 2), int(y + h / 2))     # middle point of the face
        # A yellow circle (0, 255, 255 = no blue, full green, full red) drawn
        # roughly the size of the face.
        cv2.circle(frame, center, int((w + h) / 4), (0, 255, 255), 2)
        # Write the word "biggest" just above the box. max(20, y - 8) keeps the
        # text on screen even when the face is near the very top.
        cv2.putText(frame, "biggest", (x, max(20, y - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)


def loop():
    """Read pictures, mark all faces, follow the biggest, and show the video."""
    while True:
        frame = face.read_frame()           # from Lesson 7: get one picture
        if frame is None:
            break
        faces = face.detect_faces(frame)    # from Lesson 7: find EVERY face
        target = face.biggest_face(faces)   # from Lesson 7: pick the biggest one
        draw_faces(frame, faces, target)    # new in Lesson 8: draw them all
        face.track_face(target)             # from Lesson 7: follow the biggest
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
