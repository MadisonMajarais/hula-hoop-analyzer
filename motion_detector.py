import cv2
import os


def detect_motion(video_path, output_dir, filename):
    cap = cv2.VideoCapture(video_path)
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Create video for output
    output_filename = "annotated_" + os.path.splitext(filename)[0] + ".webm"
    output_path = os.path.join(output_dir, output_filename)
    fourcc = cv2.VideoWriter_fourcc(*"VP80")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))


    frame_log = []

    success = True
    frame_num = 0
    while success:
        (success, frame) = cap.read()
        if not success:
            break

        # Detect if frame has motion
        fg_mask = bg_subtractor.apply(frame)
        fg_mask = cv2.inRange(fg_mask, 220, 255)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = [contour for contour in contours if cv2.contourArea(contour) > 4]
        has_motion = len(motion_detected) > 0

        frame_log.append({"frame": frame_num, "has_motion": has_motion, "motion_regions": len(motion_detected)})      
        frame_num += 1 

        # Draw contout frame to output
        cv2.drawContours(frame, motion_detected, -1, (0, 255, 0), 2)
        motion_only = cv2.bitwise_and(frame, frame, mask=fg_mask)
        out.write(motion_only)

    cap.release()
    out.release()

    return {"frame_log": frame_log, "output_filename": output_filename}
