import os
import numpy as np
from motion_detector import detect_motion

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

    frame_log = detect_motion(video_path)

    result = [f for f in frame_log if f["has_motion"] > 0]

    return {"total_frames": len(frame_log), "num_frames_with_motion": len(result)}



if __name__ == "__main__":
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    app.run(debug=True)
