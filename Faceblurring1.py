# -*- coding: utf-8 -*-
"""
Created on Tue Nov 12 22:25:53 2024

@author: Asus GK
"""

import numpy as np
import cv2
import sys, inspect, os
import argparse

cmd_subfolder = os.path.realpath(
    os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0], "..", "..", "Image_Lib")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

import image_utils as utils

# Membuat parser untuk argumen baris perintah agar bisa mengambil input video dari file video atau webcam
ap = argparse.ArgumentParser("Track and blur faces in video input")
ap.add_argument("-v", "--video", help="Path to video file. Defaults to webcam video")
args = vars(ap.parse_args())

# Memeriksa apakah argumen --video disediakan. Jika ya, membuka file video tersebut; jika tidak, menggunakan kamera bawaan (index 0)
if not args.get("video", False):
    camera = cv2.VideoCapture(0)
else:
    camera = cv2.VideoCapture(args["video"])

# Menginisialisasi classifier wajah dalam frame video
face_cascade = cv2.CascadeClassifier("C:/Users/Asus GK/Documents/citra digital/haarcascade_frontalface_default.xml")

# Membaca frame dari input video. Jika gagal, keluar dari loop dan menampilkan pesan error
while True:
    grabbed, frame = camera.read()
    if not grabbed:
        print("Camera read failed!")
        break

    # Menampilkan frame asli sebelum diproses
    cv2.imshow("Original Frame", frame)

    # Mengonversi frame ke gambar grayscale untuk mempermudah deteksi wajah, lalu menampilkannya
    gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imshow("Gray Image", gray_image)

    # Deteksi wajah pada gambar grayscale
    faces = face_cascade.detectMultiScale(gray_image, 1.2, 2)

    # Perulangan pada setiap wajah yang terdeteksi
    if len(faces) > 0:
        for (x, y, w, h) in faces:
            # Draw rectangle on detected face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.imshow("Detected Face Rectangle", frame)

            # Extract and show ROI (Region of Interest)
            roi = frame[y:y + h, x:x + w, :]
            cv2.imshow("Face ROI", roi)

            # Apply Gaussian blur to ROI
            blurred_roi = cv2.GaussianBlur(roi, (25, 25), 100)
            frame[y:y + h, x:x + w, :] = blurred_roi
            cv2.imshow("Blurred ROI", frame)

    # Show final output frame with blurred faces
    cv2.imshow("Output Frame", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()

def camshift_track(prev, box, termination):
    hsv = cv2.cvtColor(prev, cv2.COLOR_BGR2HSV)
    cv2.imshow("HSV Converted Frame", hsv)
    x, y, w, h = box

    # Extract and show ROI for histogram calculation
    roi = prev[y:y + h, x:x + w]
    cv2.imshow("Tracking ROI", roi)

    # Calculate and normalize histogram
    hist = cv2.calcHist([roi], [0], None, [16], [0, 180])
    cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)
    backProj = cv2.calcBackProject([hsv], [0], hist, [0, 180], 1)
    cv2.imshow("Back Projection", backProj)

    # Perform CamShift and show updated box
    (r, box) = cv2.CamShift(backProj, tuple(box), termination)
    return box

def camshift_face_track():
    face_cascade = cv2.CascadeClassifier("C:/Users/Asus GK/Documents/citra digital/haarcascade_frontalface_default.xml")
    termination = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
    ALPHA = 0.5

    camera = cv2.VideoCapture(0)
    face_box = None

    print("Waiting to get first face frame...")
    while face_box is None:
        grabbed, frame = camera.read()
        if not grabbed:
            raise EnvironmentError("Camera read failed!")
        image_prev = cv2.pyrDown(frame)
        face_box = utils.detect_face(face_cascade, image_prev)
        cv2.imshow("Downsampled Frame", image_prev)

    print("Face found!")
    prev_frames = image_prev.astype(np.float32)
    while True:
        _, frame = camera.read()
        image_curr = cv2.pyrDown(frame)
        cv2.accumulateWeighted(image_curr, prev_frames, ALPHA)
        cv2.imshow("Accumulated Weighted Frame", prev_frames)

        image_curr = cv2.convertScaleAbs(prev_frames)
        cv2.imshow("Converted Scale Abs Frame", image_curr)

        if face_box is not None:
            face_box = camshift_track(image_curr, face_box, termination)
            cv2.rectangle(image_curr, (face_box[0], face_box[1]), (face_box[0] + face_box[2], face_box[1] + face_box[3]),
                          (255, 0, 0), 2)
            cv2.imshow("Tracked Face Box", image_curr)

        else:
            face_box = utils.detect_face(face_cascade, image_curr)
            cv2.imshow("Detected Face (CamShift)", image_curr)

        cv2.imshow("Output (CamShift)", image_curr)
        key = cv2.waitKey(1)
        if key & 0xFF == ord('q'):
            break
        elif key & 0xFF == ord('r'):
            print("Reseting face detection!")
            face_box = None
