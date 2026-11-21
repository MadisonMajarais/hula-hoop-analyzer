import pandas as pd
import numpy as np

def compute_hoop_stats(frame_log, fps):

    # Build dataframe
    df = pd.DataFrame([f["hoop_pos"] or {} for f in frame_log])

    #  Check table not empty
    if "x_pos" not in df:
        return {"orbits": None, "detection_rate": 0.0}


    df["time"] = df.index / fps

    detected = df["x_pos"].notna()
    detection_rate = float(detected.mean())

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
    # computer count of crossings
    

    


    # compute direction

     #  Compute hoop speed  

    # compute hoop
    
if __name__ == "__main__":
    from hoop_tracker import track_hoop
    result = track_hoop("static/uploads/20260921_145738.mp4", "static/outputs", "hoop_test.webm")
    compute_hoop_stats(result["frame_log"], result["fps"])
