import cv2

MIN_AREA = 5

def find_circle_center(frame_log):
    for frame in frame_log:
        raw_frame = frame["raw_frame"]
        grey_scale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.medianBlur(grey_scale, 5)

        circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1, 50)

        if circles is not None:
            for circle in circles:
                _, _, r = circle


def track_tape(video_path, output_csv_path, hoop_diameter):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video {video_path}")


    frame_log = []

    success, frame = cap.read()
    while success:

        # Convert to HSV colours
        raw_frame = frame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_range = (40, 80, 80)
        upper_range = (85, 255, 255)
        frame = cv2.inRange(frame, lower_range, upper_range)

        # Remove small noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        frame = cv2.morphologyEx(frame, cv2.MORPH_OPEN, kernel)

        # Find largest contour
        contours, _ = cv2.findContours(frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            # Skip if no green found
            success, frame = cap.read()
            frame_log.append({"center_pos": None, "raw_frame": raw_frame})
            continue

        largest = max(contours, key=cv2.contourArea)

        if cv2.contourArea(largest) < MIN_AREA:
            success, frame = cap.read()
            frame_log.append({"center_pos": None, "raw_frame": raw_frame})
            continue

        # Get center of tape

        M = cv2.moments(largest)

        if M["m00"] == 0:
            #  Skips if area is 0
            success, frame = cap.read()
            frame_log.append({"center_pos": None, "raw_frame": raw_frame})
            continue

        # Find avg position of the center (ex. adding all x pos / area (i.e. num pixels))
        cx, cy = M["m10"] / M["m00"], M["m01"] / M["m00"]

        frame_log.append({"center_pos": {"x_pos": cx, "y_pos": cy}, "raw_frame": raw_frame})

        success, frame = cap.read()
    