import pandas as pd
import numpy as np
from hoop_plot import plot_hoop_data

MIN_ORBIT_SEC = 0.3
MAX_ORBIT_SEC = 2.0
MIN_SWING_FRAC = 0.3

# Outputs dataframe with hoop data and window
def build_hoop_signals(frame_log, fps):
    # Build dataframe
    df = pd.DataFrame([f["hoop_pos"] or {} for f in frame_log])

    #  Check table not empty
    if "x_pos" not in df:
        return None, None


    df["time"] = df.index / fps

    detected = df["x_pos"].notna()
    # detection_rate = float(detected.mean())

    # Remove outliers

    typical = df["width"].median()
    bad = (df["width"] < 0.5 * typical) | (df["width"] > 1.5 * typical)
    df.loc[bad, ["x_pos", "y_pos", "left", "right", "width", "angle"]] = np.nan

    #  Fill gaps
    MAX_GAP_SEC = 0.15
    max_gap = max(1, round(MAX_GAP_SEC * fps))
    cols =["x_pos", "y_pos", "left", "right", "width", "angle"]

    # Fills up to max gaps frames
    df[cols] = df[cols].interpolate(limit=max_gap, limit_area="inside")


    print(df.head())
    print(df.isna().mean())
    print(len(df) == len(frame_log))

    # Get x pos of hoop relative to person. Only count hoop movements and
    # ignore person walking, etc.
    num_orbit_frames = estimate_num_orbit_frames(df["x_pos"], fps)
    if num_orbit_frames is None:
        return None, None
    amp_window = 2 * num_orbit_frames

    x = df["x_pos"]
    drift = x.rolling(num_orbit_frames, center=True, min_periods=1).mean()
    swing = x - drift

    # Normalize to range from -1 to 1
    amplitude = (swing.rolling(amp_window, center=True, min_periods=1).max()
                 - swing.rolling(amp_window, center=True, min_periods=1).min()) / 2
    offset = swing / amplitude
    # Handle cases where hoop barely moves
    offset[amplitude < 1] = np.nan

    # Save the columns in the dataframe
    df["swing"] = swing
    df["offset"] = offset
    df["amplitude"] = amplitude
    df["drift"] = drift

    return df, num_orbit_frames

# Return number of frames of estimated orbit window
def estimate_num_orbit_frames(x, fps):
    # Interpolate x values to fill in gaps and find rolling average of a sliding window
    x = x.interpolate(limit_direction="both")
    x = x - x.rolling(round(MAX_ORBIT_SEC * fps), center=True, min_periods=1).mean()
    x = x.to_numpy()

    # Shift and find how similar x positions are to itself
    ac = np.correlate(x, x, mode="full")[len(x) - 1:]

    # Find the shift that matches best, meaning a new orbit begins
    lo = max(1, round(MIN_ORBIT_SEC * fps))
    hi = min(len(ac) - 1, round(MAX_ORBIT_SEC * fps))
    if hi <= lo:
        return None #Video too short
    # Find estimated frame when new orbit begins
    return lo + int(np.argmax(ac[lo:hi + 1]))


def compute_hoop_stats(frame_log, fps):

    df, num_orbit_frames = build_hoop_signals(frame_log, fps)


    print(num_orbit_frames)

    plot_hoop_data(df, MIN_SWING_FRAC)



    # compute direction

     #  Compute hoop speed  

    # compute hoop
    
if __name__ == "__main__":
    from hoop_tracker import track_hoop
    result = track_hoop("static/uploads/20260921_145738.mp4", "static/outputs", "hoop_test.webm")
    compute_hoop_stats(result["frame_log"], result["fps"])
