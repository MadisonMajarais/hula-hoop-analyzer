import cv2
import math
import os

MIN_AREA = 100

def track_tape(video_path, output_dir, filename):
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
    output_filename = "tape_" + os.path.splitext(filename)[0] + ".webm"
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
        lower_range = (22, 100, 70)
        upper_range = (38, 255, 255)

        mask = cv2.inRange(hsv, lower_range, upper_range)

        # Ignore anything that isn't moving (static background objects)
        fg_mask = bg_subtractor.apply(frame)
        fg_mask = cv2.inRange(fg_mask, 220, 255)
        fg_mask = cv2.dilate(fg_mask, kernel)
        mask = cv2.bitwise_and(mask, fg_mask)

        # Remove small noise
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Keep only tape pixels
        tape = cv2.bitwise_and(frame, frame, mask=mask)
        # Find largest contour
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            # Skip if no green found
            frame_log.append({"tape_pos": None})
            out.write(tape)
            success, frame = cap.read()
            continue

        largest = max(contours, key=cv2.contourArea)

        if cv2.contourArea(largest) < MIN_AREA:
            frame_log.append({"tape_pos": None})
            out.write(tape)
            success, frame = cap.read()
            continue

        # Get center of tape

        M = cv2.moments(largest)

        if M["m00"] == 0:
            #  Skips if area is 0
            frame_log.append({"tape_pos": None})
            out.write(tape)
            success, frame = cap.read()
            continue

        # Find avg position of the center (ex. adding all x pos / area (i.e. num pixels))
        cx, cy = M["m10"] / M["m00"], M["m01"] / M["m00"]
        
        frame_log.append({"tape_pos": {"x_pos": cx, "y_pos": cy}})

        # Draw tape center
        cv2.circle(tape, (int(cx), int(cy)), 10, (0, 0, 255), 2)
        out.write(tape)

        success, frame = cap.read()

    cap.release()
    out.release()

    return {"frame_log": frame_log, "fps": fps, "output_filename": output_filename}

if __name__ == "__main__":
    result = track_tape("static/uploads/20260921_145738.mp4", "static/outputs", "test.mp4")
    found = sum(1 for f in result["frame_log"] if f["tape_pos"] is not None)
    print(f"Tape found in {found}/{len(result['frame_log'])} frames")

    