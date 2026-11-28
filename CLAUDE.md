# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Flask + OpenCV app that analyzes hula hooping videos. The whole hoop (blue) is tracked by colour; its centre's left/right swing relative to the body gives the orbit count, RPM, and later direction and speed. On upload, `app.py` runs `hoop_tracker.track_hoop` → `hoop_stats.compute_hoop_stats`. `tape_tracker.py` is a shelved earlier approach (tape measures spin, not orbit).

## Commands

```bash
pip install -r requirements.txt   # inside venv/
python app.py                     # dev server at http://127.0.0.1:5000/
python hoop_stats.py              # tracker + stats on the test video
```

`venv/` is a WSL venv (`bin/`, not `Scripts/`). From Windows: `wsl -d Ubuntu -- bash -c "cd /mnt/c/Users/Madis/Documents/Coding/hula-hoop-analyzer && venv/bin/python <script>"`. No tests, linter, or build step.

Test video `static/uploads/20260921_145738.mp4`: 734 frames, 30 fps, portrait, side-on. Hand count **35 orbits**; orbit ≈ 20 frames (~90 RPM).

## Architecture

- **Request flow:** `index.html` `fetch`es `POST /upload`, which returns JSON (`{"error": ...}` + 4xx on failure; stats, per-frame `hoop_data`, `video_url` on success). Synchronous, no database; the frontend maps `video.currentTime * fps` to a log index. Uploads go to `static/uploads/`, annotated videos to `static/outputs/` (both gitignored).
- **Tracker contract:** `fn(video_path, output_dir, filename)` → `{"frame_log", "fps", "output_filename"}`; raises `ValueError` for unreadable video or bad fps/dimensions. Output is WebM/VP8 (`VP80`) for browser playback. Exactly one log entry per frame (`None` if not found) so index == frame and time = `index / fps`. No raw frames in the log; values must be plain floats (JSON-safe).
- **`hoop_tracker.py`:** HSV mask (blue range hardcoded; TODO colour picker) + morphological open. No waist band (must work for any height/framing). Uses **all** mask pixels, not the largest contour, because the body splits the hoop. Edges = 1st/99th percentile of x; `angle` from mask moments (positive = right side lower).
- **`hoop_stats.py`:** `build_hoop_signals` → DataFrame (row == frame) with width-outlier removal, short-gap fill, `drift` (rolling mean over 1 orbit), `amplitude` (over 2 orbits), and `offset` ≈ −1…+1. Orbit length comes from autocorrelation per video (`estimate_num_orbit_frames`); never hardcode it. `count_revolutions` is a hysteresis counter (±0.3). `compute_hoop_stats` returns a JSON-safe dict, not the DataFrame; RPM is measured between first and last crossing.
- **`hoop_plot.py`:** debug-only matplotlib plot to `static/outputs/offset.png`; matplotlib is deliberately not in `requirements.txt`.

## Domain

- Filmed from the **front or side**, at or slightly above waist height, so the hoop is a flat ellipse — circle detection doesn't work. "Near/far" means relative to the camera.
- **Orbit vs spin:** the hoop's centre orbits the body; the hoop spins on itself more slowly (`spins ≈ orbits × (1 − waist_r / hoop_r)`). Any mark on the hoop counts spins. User-facing "revolution" = orbit. Both go the same direction.
- **Orbit signal:** centre x ≈ `body_x + d·cos(2π·t / period)`, one cycle per orbit, from any horizontal angle. Hoop edges are never occluded, so the edge midpoint is unbiased. If body movement or big speed changes break the rolling-mean drift removal, use MediaPipe hip x instead.
- **Direction (TODO):** x alone can't tell CW from CCW. Plan: depth cue `width − rolling mean(width)` (nearer = wider; fallback `y_pos`, nearer = lower). Centre moving right while near ⇒ CCW from above. Validate on the test video.
- **Speed (TODO):** `hoop_diameter / median(width)` gives m/px; speed = `2π · orbit_radius · rpm / 60`, orbit radius ≈ median amplitude.

## Open items

- Remove the `plot_hoop_data` import/call from `compute_hoop_stats`; call it from `hoop_plot.py`'s `__main__`.
- `compute_hoop_stats` returns `None` on failure and `app.py` indexes into it; return the usual dict with `None`s. `app.py` doesn't catch tracker `ValueError`.
- Debug `print`s left in `hoop_stats.py`.
- Planned: frontend Chart.js plot of `offset` with a cursor synced to the video.
