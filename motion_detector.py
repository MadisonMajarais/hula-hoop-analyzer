import cv2

def detect_motion(video_path):
    cap = cv2.VideoCapture(video_path)
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)

    frame_log = []

    success = True
    frame_num = 0
    while success:
        (success, frame) = cap.read()
        if not success:
            break
        fg_mask = bg_subtractor.apply(frame)
        fg_mask = cv2.inRange(fg_mask, 200, 255)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = [contour for contour in contours if cv2.contourArea(contour) > 4]
        has_motion = len(motion_detected) > 0

        frame_log.append({"frame": frame_num, "has_motion": has_motion, "motion_regions": len(motion_detected)})      
        frame_num += 1 

    cap.release()

    return frame_log
