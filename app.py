import os
import cv2
import numpy as np

from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename

app = Flask(__name__)
bootstrap = Bootstrap(app)

UPLOAD_DIR = os.path.join(app.static_folder, "uploads")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("video")
    if not file or file.filename == "":
        return render_template("index.html", error="Please choose a video file")

    filename = secure_filename(file.filename)
    video_path = os.path.join(UPLOAD_DIR, filename)
    file.save(video_path)

    cap = cv2.VideoCapture(video_path)
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)

    success = True
    # while success:
    #     (success, frame) = cap.read()
    #     if not success:
    #         break
    #     fg_mask = bg_subtractor.apply(frame)
    #     fg_mask = cv2.inRange(fg_mask, 200, 255)
    #     fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, cv2.MORPH_RECT)
    #     contour = cv2.findContours 

    return {"result": "Success"}



if __name__ == "__main__":
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    app.run(debug=True)
