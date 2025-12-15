import cv2
import numpy as np
from picamera2 import Picamera2

cv2.startWindowThread()

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

draw = True

lower_red1 = np.array([0, 70, 50])
upper_red1 = np.array([4, 255, 255])
lower_red2 = np.array([170, 70, 50])
upper_red2 = np.array([180, 255, 255])
low_black = np.array([0, 0, 0])
high_black = np.array([180, 255, 40])


while True:
    # Capture frame
    cap = picam2.capture_array("main")

    # # Convert to HSV
    # hsv = cv2.cvtColor(center_region, cv2.COLOR_BGR2HSV)
    # # Define red color range (two ranges for HSV red)



    # # Find contours in the red mask
    # contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Draw rectangle on original frame
    cv2.rectangle(cap, (220, 140), (420, 340), (255, 255, 255), 1)
    frame = cap[140:340, 220:420]
    cv2.rectangle(cap, (0,240), (100,480), (255, 255, 255), 1)
    cv2.rectangle(cap, (540,240), (640,480), (255, 255, 255), 1)
    left_frame = cap[0:100, 240:480]
    right_frame = cap[240:480, 540:640]
    # frame_gaussed = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv = cv2.cvtColor(left_frame, cv2.COLOR_BGR2HSV)
    hsv = cv2.cvtColor(right_frame, cv2.COLOR_BGR2HSV)

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)
    black_mask = cv2.inRange(hsv, low_black, high_black)

    black_contours, _ = cv2.findContours(black_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    if black_contours:
        cv2.drawContours(left_frame, black_contours, -1, (0, 255, 0), 2)


    contours, _ = cv2.findContours(black_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    for i in contours:
        if cv2.contourArea(i) > 200:
            cv2.drawContours(frame, i, -1, (0, 0, 255), 2)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        # Show original frame only
    if draw:
        cv2.imshow("Video Frame", cap)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
