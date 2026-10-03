import os
import numpy as np
from motion_detector import detect_motion
from datetime import datetime

from flask import Flask, render_template, request, url_for
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024
bootstrap = Bootstrap(app)

UPLOAD_DIR = os.path.join(app.static_folder, "uploads")
OUTPUT_DIR = os.path.join(app.static_folder, "outputs")
ALLOWED_VIDEO_EXTENSIONS = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm"}

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")


@app.errorhandler(413)
def upload_too_large(_error):
    return {"error": "Video must be smaller than 500 MiB."}, 413

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("video")
    if file is None or file.filename == "":
        return {"error": "Please choose a video file."}, 400

    filename = secure_filename(file.filename)
    if not filename:
        return {"error": "Please choose a valid video filename."}, 400
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}{ext}"
    if ext.lower() not in ALLOWED_VIDEO_EXTENSIONS:
        return {"error": "Unsupported file type. Choose AVI, M4V, MKV, MOV, MP4, or WEBM."}, 400

    video_path = os.path.join(UPLOAD_DIR, filename)
    file.save(video_path)


    result = detect_motion(video_path, OUTPUT_DIR, filename)

    motion_frames = [f for f in result["frame_log"] if f["has_motion"] > 0]

    return {"total_frames": len(result["frame_log"]),
             "num_frames_with_motion": len(motion_frames),
             "video_url": url_for("static", filename="outputs/" + result["output_filename"])
             }



if __name__ == "__main__":
    app.run(debug=True)
