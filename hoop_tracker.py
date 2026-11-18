import cv2
import math
import os
import numpy as np

MIN_AREA = 50
REMOVE_BACKGROUND = False

def track_hoop(video_path, output_dir, filename):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        cap.release()
        raise ValueError(f"Could not open video {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    if (not math.isfinite(fps) or not math.isfinite(width)
        or not math.isfinite(height) or fps <= 0 or width <= 0 or height <= 0):
        cap.release()
        raise ValueError("Video fps or dimensions is invalid")

    width = int(width)
    height = int(height)

     # Create video for output
    output_filename = "hoop_" + os.path.splitext(filename)[0] + ".webm"
    output_path = os.path.join(output_dir, output_filename)
    fourcc = cv2.VideoWriter_fourcc(*"VP80")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    
    frame_log = []

    success, frame = cap.read()

    bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

    while success:

        # Convert to HSV colours
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_range = (95, 70, 30)
        upper_range = (130, 255, 255)

        # Create mask that detects hoop
        # TODO: Make colour picker for hoop
        mask = cv2.inRange(hsv, lower_range, upper_range)

        # Ignore anything that isn't moving (static background objects)
        if REMOVE_BACKGROUND:
            fg_mask = bg_subtractor.apply(frame)
            fg_mask = cv2.inRange(fg_mask, 220, 255)
            fg_mask = cv2.dilate(fg_mask, kernel)
            mask = cv2.bitwise_and(mask, fg_mask)

        # Remove small noise
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Output frame: hoop pixels only when removing background, else the full frame
        hoop = cv2.bitwise_and(frame, frame, mask=mask) if REMOVE_BACKGROUND else frame.copy()
        
        # Find the center, left, right
        ys, xs = np.nonzero(mask)
        left = np.percentile(xs, 1)
        right = np.percentile(xs, 99)
        top = np.percentile(ys, 1)
        bottom = np.percentile(ys, 99)
        c_x = (left + right) / 2
        c_y = (top + bottom) / 2

        # Find angle
        m = cv2.moments(mask, binaryImage=True)
        angle = 0.5 * math.degrees(math.atan2(2 * m["mu11"], m["mu20"] - m["mu02"]))
        
        frame_log.append({"hoop_pos": {"x_pos": c_x, "y_pos": c_y, "left": left, "right": right},
                          "hoop_angle": angle})

        # Draw tape center
        cv2.circle(hoop, (int(c_x), int(c_y)), 10, (0, 0, 255), 2)
        out.write(hoop)

        success, frame = cap.read()

    cap.release()
    out.release()

    return {"frame_log": frame_log, "fps": fps, "output_filename": output_filename}

if __name__ == "__main__":
    result = track_hoop("static/uploads/20260921_145738.mp4", "static/outputs", "test.mp4")
    found = sum(1 for f in result["frame_log"] if f["hoop_pos"] is not None)
    print(f"Hoop found in {found}/{len(result['frame_log'])} frames")

    