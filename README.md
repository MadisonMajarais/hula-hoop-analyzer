# Hula Hoop Analyzer

A Flask web app that detects motion in an uploaded video using OpenCV. Upload a video and currently it will:

- Run background subtraction (MOG2) frame-by-frame to detect motion
- Report how many frames contain motion
- Generate an annotated output video showing only the moving regions (background removed)

## Goal

I grew up hula hooping a lot and thought it would be fun to use computer vision to track how the hoop moves while hula hooping.

Note this project is currently ongoing.

I recorded videos hula hooping and added a bright piece of tape onto the hoop to help track the angle and speed the hooop moves.  I plan on using OpenCV to help track the movements, then I'll compile the data and report stats.

## Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running

```bash
python3 app.py
```

Then open `http://127.0.0.1:5000/` in a browser.

## Usage

1. Choose a video file and click Upload.
2. Once processing finishes, the page shows the total frame count and how many frames had motion, plus the annotated output video.

## Project structure

- `app.py` — Flask routes (upload handling, rendering)
- `motion_detector.py` — OpenCV motion detection logic
- `templates/` — HTML pages
- `static/uploads/` — uploaded videos (gitignored)
- `static/outputs/` — generated annotated videos (gitignored)
