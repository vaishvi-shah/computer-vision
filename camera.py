import cv2
import numpy as np
from picamera2 import Picamera2
from frames import Frame
import time
import serial

default_steering_value = 90
KP = 0.01  # Proportional gain for steering adjustment
# # Replace '/dev/ttyUSB0' with your serial port
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)  # Wait for the connection to initialize



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
left_frame = Frame(cap, 0, 40, 240, 480,[low_black], [high_black])
right_frame = Frame(cap, 600, 640, 240, 480,[low_black], [high_black])
counter = 0

fps = 0
frame_count = 0
start_time = time.time()

while True:
    # Capture frame
    cap = picam2.capture_array("main")
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
    left_area = left_frame.get_areas()
    right_area = right_frame.get_areas() 

    steering_value = default_steering_value + KP * (left_area-right_area)   
    steering_value = max(30, min(150, steering_value)) + 100  # Clamp to [30, 150]
    ser.write(f"{steering_value:.2f}\n".encode())

    cv2.putText(cap, f"Steering: {steering_value:.2f}", (200, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

    cv2.putText(cap, str(left_area), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    cv2.putText(cap, str(right_area), (500, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

    right_frame.update(cap)
    right_frame.find_contours()

    frame_count += 1
    elapsed = time.time() - start_time
    if elapsed > 1.0:
        fps = frame_count // elapsed
        frame_count = 0

        start_time = time.time()
    
    if draw:
        # Display FPS on frame
        cv2.putText(cap, f"FPS: {fps:.2f}", (200, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        cv2.imshow("Video Frame", cap)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
ser.close()
        

cv2.destroyAllWindows()
