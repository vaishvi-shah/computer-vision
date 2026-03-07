import cv2
import numpy as np
from picamera2 import Picamera2
from frames import Frame
import time
import serial

# Green is left, red is right

default_steering_value = 90
KP = 0.01  # Proportional gain for steering adjustment
# # Replace '/dev/ttyUSB0' with your serial port
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
time.sleep(2)  # Wait for the connection to initialize

turning_time = time.time()

cv2.startWindowThread()

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

draw = True
turning = False
lower_red1 = np.array([0, 100, 100])
upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([180, 100, 100])
upper_red2 = np.array([180, 255, 255])
low_black = np.array([0, 0, 0])
high_black = np.array([180, 200, 60])
low_green = np.array([40, 70, 50])
high_green = np.array([80, 255, 255])
low_blue = np.array([100, 150, 0])
high_blue = np.array([140, 255, 255])
low_orange = np.array([10, 100, 100])
high_orange = np.array([25, 255, 255])
direction = None
cap = picam2.capture_array("main")

middle_frame = Frame(cap, 220, 420, 140, 340,[lower_red1, lower_red2], [upper_red1, upper_red2], [low_green], [high_green])
left_frame = Frame(cap, 0, 40, 240, 480,[low_black], [high_black])
right_frame = Frame(cap, 600, 640, 240, 480,[low_black], [high_black])
low_frame = Frame(cap, 60, 580, 410, 470,[low_blue], [high_blue], [low_orange], [high_orange])
counter = 0

fps = 0
frame_count = 0
start_time = time.time()
steering_value = default_steering_value + 100

while True:
    # Capture frame
    cap = picam2.capture_array("main")

    middle_frame.update(cap)
    red_contours, green_contours = middle_frame.find_contours(is_red=True, colour=(255,0,0), colour2=(0,0,255))
    middle_area, middle_colour = middle_frame.get_areas(red_contours, green_contours) # if middle_colour = 1 = red if middle_colour = 2 = green



    left_frame.update(cap)
    left_contours = left_frame.find_contours()
    right_frame.update(cap)
    right_contours = right_frame.find_contours()
    low_frame.update(cap)
    left_area, _ = left_frame.get_areas(left_contours)
    right_area, _ = right_frame.get_areas(right_contours)

    blue_contours, orange_contours = low_frame.find_contours(colour=(0,255,0), colour2=(255,0,0))
    low_area, bottom_colour = low_frame.get_areas(blue_contours, orange_contours) # if bottom_colour = 1 = blue if bottom_colour = 2 = orange
    if low_area != 0:
        if low_area > 10000:
            blue_contours = None
            orange_contours = None

        elif low_area > 5000:
            if bottom_colour == 1:
                low_frame.add_lines(bottom_colour)
            elif bottom_colour == 2:
                low_frame.add_lines(bottom_colour)

    if direction == "clockwise" and bottom_colour == 2 or direction == "counterclockwise" and bottom_colour == 1:
        turning = True



    # getting the default steer value 
    steering_value = default_steering_value + KP * (left_area - right_area)
    steering_value = max(30, min(150, steering_value)) + 100  # Clamp to [30, 150]

    # turning section
    if turning:

        if time.time() - turning_time > 2:
            print("success")
            turning_time = time.time()
            turning = False
        else:
            temp_value = low_frame.get_turn_value(direction)
            if temp_value is not None:
                steering_value = temp_value


    # turning after seeing the middle colours

    if middle_area < 5000:
        middle_colour = None

    if middle_colour is not None:
        print("old steering_value", steering_value)
        if middle_colour == 1: # it is RED
            temp_value = middle_frame.get_turn_value(direction="clockwise")
        elif middle_colour == 2: # it is GREEN
            temp_value = middle_frame.get_turn_value(direction="counterclockwise")
        if temp_value is not None:
            steering_value = temp_value
            print("new steering_value", steering_value)


    blue_count = low_frame.get_line_count(1)
    orange_count = low_frame.get_line_count(2)

    if direction == None:
        if blue_count == 0 and orange_count > 0: # turn clockwise if orange
            direction = "clockwise"
            print(direction)
        elif orange_count == 0 and blue_count > 0: # turn counterclockwise if blue
            direction = "counterclockwise"
            print(direction)

    ser.write(f"{steering_value:.2f}\n".encode())

    cv2.putText(cap, f"Steering: {steering_value:.2f}", (200, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

    cv2.putText(cap, str(left_area), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    cv2.putText(cap, str(right_area), (500, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    cv2.putText(cap, f"orange: {str(orange_count)}", (10, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    cv2.putText(cap, f"blue: {str(blue_count)}", (500, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

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
