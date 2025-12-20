import cv2
import numpy as np
from picamera2 import Picamera2
from frames import Frame

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
high_black = np.array([180, 200, 60])

cap = picam2.capture_array("main")

red_frame = Frame(cap, 220, 420, 140, 340,[lower_red1, lower_red2], [upper_red1, upper_red2])
left_frame = Frame(cap, 0, 100, 240, 480,[low_black], [high_black])
right_frame = Frame(cap, 540, 640, 240, 480,[low_black], [high_black])

while True:
    # Capture frame

    cap = picam2.capture_array("main")
    # # Convert to HSV
    # hsv = cv2.cvtColor(center_region, cv2.COLOR_BGR2HSV)
    # # Define red color range (two ranges for HSV red)



    # # Find contours in the red mask
    # contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Draw rectangle on original frame
    # cv2.rectangle(cap, (220, 140), (420, 340), (255, 255, 255), 1)
    # frame = cap[140:340, 220:420]

    # cv2.rectangle(cap, (0,240), (100,480), (255, 255, 255), 1)
    # cv2.rectangle(cap, (540,240), (640,480), (255, 255, 255), 1)
    # left_frame = cap[240:480, 0:100]
    # right_frame = cap[240:480, 540:640]
    # # frame_gaussed = cv2.GaussianBlur(frame, (5, 5), 0)
    # hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # hsv_l = cv2.cvtColor(left_frame, cv2.COLOR_BGR2HSV)
    # hsv_r = cv2.cvtColor(right_frame, cv2.COLOR_BGR2HSV)

    # mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    # mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    # red_mask = cv2.bitwise_or(mask1, mask2)
    # black_left_mask = cv2.inRange(hsv_l, low_black, high_black)
    # black_right_mask = cv2.inRange(hsv_r, low_black, high_black)

    # left_contours, _ = cv2.findContours(black_left_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # if left_contours:
    #     cv2.drawContours(left_frame, left_contours, -1, (0, 0, 255), 2)

    # right_contours, _ = cv2.findContours(black_right_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # if right_contours:
    #     cv2.drawContours(right_frame, right_contours, -1, (0, 255, 0), 2)


    # contours, _ = cv2.findContours(red_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # for i in contours:
    #     if cv2.contourArea(i) > 200:
    #         cv2.drawContours(frame, i, -1, (0, 0, 255), 2)
    # if contours:
    #     largest = max(contours, key=cv2.contourArea)
    #     x, y, w, h = cv2.boundingRect(largest)
    #     cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
    #     # Show original frame only
    red_frame.update(cap)
    red_frame.find_contours(is_red=True)

    left_frame.update(cap)
    left_frame.find_contours()

    right_frame.update(cap)
    right_frame.find_contours()

    if draw:
        cv2.imshow("Video Frame", cap)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
