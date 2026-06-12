'''
1. make it run and stop when it sees black
2. if i see orange on floor, i turn right, blue turn left
'''


# imports!
import cv2
import numpy as np
from picamera2 import Picamera2
from frames import Frame
import time
import serial
import bno055 

CALIBRATION_FILE = "src/sensors/bno055_calibration.json"
bno055.initialize()
sensor = bno055.sensor
bno055.load_calibration()
SHOW_VID = True
DEFAULT_STEER_ANGLE = 90
LINE_COUNT = 4

KP = 0.01
KD = 0.001

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
time.sleep(2)
steering = 100 + DEFAULT_STEER_ANGLE
stop = False
speed = 0000

blue_count = 0
orange_count = 0
direction = ''

frame_count = 0
fps = 0
frame_time = time.time()

stop = False
stop_time = time.time()

turning = False
turning_time = time.time()

# defining colour ranges
bottom_black = np.array([0, 0, 0])
high_black = np.array([180, 200, 60])
bottom_blue = np.array([100, 50, 60])
high_blue = np.array([140, 255, 255])
bottom_orange = np.array([10, 60, 100])
high_orange = np.array([25, 255, 255])

# Function to navigate straight along the wall based on the number of black pixels on either wall
# if more black on a wall, turn steering the other way proportional to difference of black pixels


# the IMU

print("Reading gyro heading. Press Ctrl+C to exit.")
cal_status = sensor.calibration_status
heading = bno055.get_heading()
if heading is not None:
    print(f"\rHeading: {heading:7.2f}° | Cal Status (S,G,A,M): {cal_status}", end="")
else:
    print("\rCould not read heading.", end="")
time.sleep(0.1)

# the IMU finished

def navigate_wall():
    left_frame.update(cap)
    right_frame.update(cap)

    left_contours = left_frame.find_contours()
    right_contours = right_frame.find_contours()

    left_area, _ = left_frame.get_areas(left_contours)
    right_area, _ = right_frame.get_areas(right_contours)

    # getting the default steer value 
    steering_value = DEFAULT_STEER_ANGLE + KP * (left_area - right_area)
    steering_value = max(30, min(150, steering_value))  # Clamp to [30, 150]

    # print(f"Left Area: {left_area} | Right Area: {right_area} | Steering: {steering}")    

    return int(steering_value)

# execution of main program
cv2.startWindowThread()

# initializing the camera
print("-- INITIALIZING CAMERA --")
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (320, 240)}))
picam2.start()
cap = picam2.capture_array("main")

# initializing frames
left_frame = Frame(cap, 0, 20, 120, 240,[bottom_black], [high_black])
right_frame = Frame(cap, 300, 320, 120, 240,[bottom_black], [high_black])
bottom_frame = Frame(cap, 100, 220, 200, 240,[bottom_blue], [high_blue], [bottom_orange], [high_orange])

print("ENTERING THE WHILE LOOP")

while True:
    cap = picam2.capture_array("main")
    gyro = bno055.get_heading()
    desired_heading = 0
    steering = 100 + navigate_wall()
    speed = 0000

    if time.time() - turning_time > 2:
        bottom_frame.update(cap)
        blue_contours, orange_contours = bottom_frame.find_contours(colour=(255,255,0), colour2=(0,127,255))
        bottom_area, bottom_colour = bottom_frame.get_areas(blue_contours, orange_contours) # if bottom_colour = 1 = blue if bottom_colour = 2 = orange
        # print("GOT THE AREAS")

        if bottom_area != 0 and bottom_area > 1600:
            # print(time.time(), "--Detected turn color--")
            turning_time = time.time()
            turning = True # This is only used for debug purposes to indicate end if turn
            if bottom_colour == 1:
                blue_count += 1
                print(f"BLUE: {blue_count}")
                if not direction:
                    direction = "CWR"
            elif bottom_colour == 2:
                orange_count += 1
                print(f"ORANGE: {orange_count}")
                if not direction:
                    direction = "CCWL"
    else:
        # Debuf condition to indicate end of turn
        if turning:
            # print(time.time(), "--DONE TURNING--")
            turning = False

    # if middle_area >= 5000:
    #     speed = 1022
    #     print("SAW BLACK ----- STOPPING")
    # else:
    #     speed = "0100"

    if orange_count >= LINE_COUNT or blue_count >= LINE_COUNT:
        if not stop:
            stop_time = time.time()
        stop = True
    
    if stop:
        if(time.time() - stop_time > 1):
            print("Stopping")
            speed = 1022
            ser.write(f"1901022\n".encode())
            ser.flush()
            break


    if (SHOW_VID):
        cv2.putText(cap, f"Steer: {steering:.2f}", (100, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
        cv2.putText(cap, f"O: {str(orange_count)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,127,255), 1)
        cv2.putText(cap, f"B: {str(blue_count)}", (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,127,0), 1)

        frame_count += 1
        elapsed = time.time() - frame_time
        if elapsed > 1.0:
            fps = frame_count // elapsed
            frame_count = 0

            frame_time = time.time()
        cv2.putText(cap, f"FPS: {fps:.2f}", (220, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)            

        cv2.imshow("Video Frame", cap)


    ser.write(f"{steering}{speed}\n".encode())
    ser.flush()
    time.sleep(0.01)
    # print(f"sent value: heading: {steering} speed: {speed}")
    if cv2.waitKey(1) & 0xFF == ord('q'):
        ser.write(f"1901022\n".encode())
        ser.flush()
        break
ser.close()
        

cv2.destroyAllWindows()
