import math
import warnings

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

# Gaps shorter than this (tape briefly lost) are filled by interpolation.
# Longer gaps are treated as the tape being hidden behind the body.
MAX_GAP_SEC = 0.15
# Window for estimating the hoop center (should cover about one rotation).
CENTER_WINDOW_SEC = 1.0
# Frames for the moving-average smoothing of x position.
SMOOTH_FRAMES = 3
# The tape must swing this fraction of the amplitude past the center to count
# as a crossing. Stops jitter near the center from counting extra revolutions.
HYSTERESIS_FRAC = 0.3
# Minimum detections needed to compute anything.
MIN_DETECTIONS = 10


def compute_hoop_stats(frame_log, fps, hoop_diameter=None):
    """Turn the tape tracker's per-frame log into hoop stats.

    frame_log: list of {"tape_pos": {"x_pos", "y_pos"} or None}, index == frame number
    fps: video frame rate
    hoop_diameter: real-world hoop diameter (any unit), optional. If given,
        speed is returned in that unit per second.
    """
    n = len(frame_log)
    raw_x = np.array(
        [f["tape_pos"]["x_pos"] if f["tape_pos"] else np.nan for f in frame_log],
        dtype=float,
    )
    detected = ~np.isnan(raw_x)

    stats = {
        "total_frames": n,
        "duration_sec": n / fps if fps else 0,
        "tape_detection_rate": float(detected.mean()) if n else 0.0,
        "revolutions": 0,
        "rpm": None,
        "direction": "unknown",
        "speed": None,
        "revolution_times_sec": [],
    }
    if detected.sum() < MIN_DETECTIONS:
        return stats

    # 1. Clean up the signal
    x = _fill_short_gaps(raw_x, max(1, round(MAX_GAP_SEC * fps)))
    x = _smooth(x, SMOOTH_FRAMES)

    # 2. Hoop center drifts with the hips. The sides of the hoop (leftmost and
    # rightmost tape positions) are never hidden by the body, so the center is
    # the midpoint of the rolling min and max over ~1 rotation.
    window = max(3, round(CENTER_WINDOW_SEC * fps))
    rmin = _rolling(x, window, np.nanmin)
    rmax = _rolling(x, window, np.nanmax)
    center = (rmin + rmax) / 2
    half_range = (rmax - rmin) / 2  # local hoop radius in pixels
    with np.errstate(invalid="ignore", divide="ignore"):
        # -1 = left side of hoop, +1 = right side
        offset = np.where(half_range >= 1, (x - center) / half_range, np.nan)

    amplitude = float(np.nanmedian(half_range))
    if not math.isfinite(amplitude) or amplitude < 1:
        return stats

    # 3. Revolutions: each revolution has one left->right and one right->left
    # swing, but one of them happens mostly behind the body. Count both and use
    # whichever direction is seen more reliably.
    up = _count_crossings(offset, HYSTERESIS_FRAC)
    down = _count_crossings(-offset, HYSTERESIS_FRAC)
    crossings = up if len(up) >= len(down) else down
    times = [i / fps for i in crossings]
    stats["revolutions"] = len(crossings)
    stats["revolution_times_sec"] = times

    # 4. RPM: full revolutions between the first and last crossing
    if len(times) >= 2 and times[-1] > times[0]:
        rpm = (len(times) - 1) / (times[-1] - times[0]) * 60
        stats["rpm"] = rpm

        # 5. Speed of the hoop rim = circumference * revolutions per second
        if hoop_diameter:
            stats["speed"] = math.pi * hoop_diameter * rpm / 60

    # 6. Direction
    stats["direction"] = _direction(raw_x, offset)

    return stats


def _fill_short_gaps(x, max_gap):
    """Linearly interpolate NaN runs of length <= max_gap that have data on both sides."""
    x = x.copy()
    isnan = np.isnan(x)
    idx = np.arange(len(x))
    if (~isnan).sum() < 2:
        return x
    interp = np.interp(idx, idx[~isnan], x[~isnan])

    i, n = 0, len(x)
    while i < n:
        if not isnan[i]:
            i += 1
            continue
        j = i
        while j < n and isnan[j]:
            j += 1
        if i > 0 and j < n and (j - i) <= max_gap:
            x[i:j] = interp[i:j]
        i = j
    return x


def _smooth(x, window):
    if window <= 1:
        return x
    kernel = np.ones(window) / window
    return np.convolve(x, kernel, mode="same")


def _rolling(x, window, func):
    """Apply a NaN-aware reducer (np.nanmin, np.nanmax, ...) over a centered window."""
    half = window // 2
    padded = np.pad(x, half, constant_values=np.nan)
    windows = sliding_window_view(padded, 2 * half + 1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # all-NaN windows
        return func(windows, axis=1)


def _count_crossings(offset, threshold):
    """Frame indices where the tape swings from below -threshold to above +threshold.

    State is kept across NaN gaps, so a crossing that happens while the tape is
    hidden still counts once the tape reappears on the other side.
    """
    crossings = []
    state = None
    for i, v in enumerate(offset):
        if np.isnan(v):
            continue
        if v < -threshold:
            state = "low"
        elif v > threshold:
            if state == "low":
                crossings.append(i)
            state = "high"
    return crossings


def _direction(raw_x, offset):
    """Rotation direction as seen from above.

    Near the hoop center, the back of the hoop is hidden by the body, so a tape
    detected there is on the front. Viewed from above with the camera at the
    bottom, the front point moving to the camera's right is counterclockwise.
    """
    velocity = np.gradient(raw_x)  # NaN wherever a neighbor wasn't detected
    near_center = np.abs(offset) < 0.5
    sel = near_center & ~np.isnan(velocity) & ~np.isnan(raw_x)
    if sel.sum() < 5:
        return "unknown"

    frac_right = float((velocity[sel] > 0).mean())
    if frac_right > 0.6:
        return "counterclockwise"
    if frac_right < 0.4:
        return "clockwise"
    return "unknown"


if __name__ == "__main__":
    from tape_tracker import track_tape

    result = track_tape("static/uploads/20260921_145738.mp4", "static/outputs", "test.mp4")
    stats = compute_hoop_stats(result["frame_log"], result["fps"], hoop_diameter=1.0)
    for key, value in stats.items():
        if key != "revolution_times_sec":
            print(f"{key}: {value}")
