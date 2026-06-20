
# imports!
import cv2
import numpy as np
from picamera2 import Picamera2
from frames import Frame
import time
import serial
import bno055 

CALIBRATION_FILE = "src/sensors/bno055_calibration.json"
bno055.initialize()            # boot the IMU over I2C
sensor = bno055.sensor
bno055.load_calibration()      # apply saved accel/gyro/mag offsets if present

SHOW_VID = True                 # toggle live OpenCV preview window
DEFAULT_STEER_ANGLE = 90        # neutral/straight steering angle, sent as 100 + this
LINE_COUNT = 4                  # number of colour-line crossings before stopping

KP = 0.01       # camera nudge gain (wall pixel area difference -> small heading correction)
KD = 0.001      # (unused currently, reserved for derivative term)
KP_GYRO = 1.0   # gyro proportional gain (heading error in degrees)
TURN_ANGLE = 90 # heading change applied to the target when a turn marker is detected

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)  # serial link to the steering/speed microcontroller
time.sleep(2)  # let the serial connection settle before writing
steering = 100 + DEFAULT_STEER_ANGLE
stop = False
speed = 0000

blue_count = 0      # number of blue line crossings seen
orange_count = 0    # number of orange line crossings seen
direction = ''      # locked turn direction once first colour is seen ("CWR" or "CCWL")

frame_count = 0      # frames seen since last FPS sample
fps = 0
frame_time = time.time()

turning = False           # true while inside the post-detection "turn window"
turning_time = time.time()  # timestamp of the last colour-line detection

# defining colour ranges (HSV) used to mask each region of interest
bottom_black = np.array([0, 0, 0])
high_black = np.array([180, 200, 60])
bottom_blue = np.array([100, 50, 60])
high_blue = np.array([140, 255, 255])
bottom_orange = np.array([10, 60, 100])
high_orange = np.array([25, 255, 255])

# Function to navigate straight along the wall based on the number of black pixels on either wall
# if more black on a wall, turn steering the other way proportional to difference of black pixels


# One-off startup check: confirm gyro is readable and report calibration state before the main loop.
print("Reading gyro heading. Press Ctrl+C to exit.")
cal_status = sensor.calibration_status
heading = bno055.get_heading()
if heading is not None:
    print(f"Heading: {heading:7.2f} | Cal Status (S,G,A,M): {cal_status}")
else:
    print("Could not read heading.")
time.sleep(0.1)
target_heading = heading if heading is not None else 0  # persistent heading goal, starts pointing straight ahead

def navigate_wall(gyro_heading):
    """
    Target-heading steering, persistent version:
      - `target_heading` is a module-level value that the robot is trying
        to point at. It is NOT recomputed from scratch every frame - it
        only gets nudged (by the camera) or jumped (by a detected turn,
        handled in the main loop). This lets the gyro genuinely hold a
        heading instead of re-chasing a brand new target every iteration.
      - The camera's only job is to apply a small persistent correction to
        target_heading when it sees more wall on one side than the other.
      - The gyro's only job is to drive heading_error (target vs current)
        to zero via the proportional term below.
    """
    global target_heading

    # Refresh the side frames with the latest camera capture and re-run the
    # colour mask + contour detection so we know how much "wall" each side sees.
    left_frame.update(cap)
    right_frame.update(cap)

    left_contours = left_frame.find_contours()
    right_contours = right_frame.find_contours()

    left_area, _ = left_frame.get_areas(left_contours)
    right_area, _ = right_frame.get_areas(right_contours)

    # Small persistent nudge to the target heading, NOT a full recompute.
    # Positive = more wall on the left -> nudge target left.
    target_heading = (target_heading + KP * (left_area - right_area)) % 360
    if gyro_heading is None:
        # No gyro available: nothing to correct against, hold straight.
        return DEFAULT_STEER_ANGLE

    # Shortest signed error between the (slowly-drifting) target and the
    # current heading, wrap-safe at 0/360 (e.g. target=5, current=355 -> +10).
    heading_error = ((target_heading - gyro_heading + 180) % 360) - 180
    print(f"heading error: {heading_error}")

    # P-controller on heading_error only. Positive error (target left of
    # current) reduces steering value; negative error increases it.
    steering_value = DEFAULT_STEER_ANGLE - KP_GYRO * heading_error
    steering_value = max(30, min(150, steering_value))  # clamp to servo range

    return int(steering_value)

# execution of main program
cv2.startWindowThread()  # needed so cv2.imshow updates without blocking on this thread

# initializing the camera
print("-- INITIALIZING CAMERA --")
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (320, 240)}))
picam2.start()
cap = picam2.capture_array("main")  # grab one frame to size the ROI frames below

# initializing frames: each Frame watches a fixed region of interest (ROI) for a colour mask.
# left/right strips watch for the black wall; bottom strip watches for blue/orange turn markers.
left_frame = Frame(cap, 0, 20, 120, 240,[bottom_black], [high_black])
right_frame = Frame(cap, 300, 320, 120, 240,[bottom_black], [high_black])
bottom_frame = Frame(cap, 100, 220, 200, 240,[bottom_blue], [high_blue], [bottom_orange], [high_orange])

print("ENTERING THE WHILE LOOP")

while True:
    cap = picam2.capture_array("main")     # latest camera frame
    gyro = bno055.get_heading()            # latest raw heading (0-359 deg), or None if unavailable
    steering = 100 + navigate_wall(gyro)   # target-heading steering, offset for serial protocol
    print(f"heading: {gyro}, steer: {steering}")
    speed = 0000

    # Only look for a new turn-colour line if we're outside the "just turned" cooldown window.
    if time.time() - turning_time > 2:
        bottom_frame.update(cap)
        blue_contours, orange_contours = bottom_frame.find_contours(colour=(255,255,0), colour2=(0,127,255))
        bottom_area, bottom_colour = bottom_frame.get_areas(blue_contours, orange_contours) # if bottom_colour = 1 = blue if bottom_colour = 2 = orange
        # print("GOT THE AREAS")

        # A large enough patch of blue/orange counts as a line crossing.
        if bottom_area != 0 and bottom_area > 1600:
            # print(time.time(), "--Detected turn color--")
            turning_time = time.time()  # restart the cooldown window
            turning = True # This is only used for debug purposes to indicate end if turn
            if bottom_colour == 1:
                blue_count += 1
                print(f"BLUE: {blue_count}")
                if not direction:
                    direction = "CWR"  # lock turn direction on first colour seen
                target_heading = (target_heading - TURN_ANGLE) % 360  # blue = turn right
            elif bottom_colour == 2:
                orange_count += 1
                print(f"ORANGE: {orange_count}")
                if not direction:
                    direction = "CCWL"
                target_heading = (target_heading + TURN_ANGLE) % 360  # orange = turn left
    else:
        # Debug: mark end of turn window
        if turning:
            turning = False

    # Once either colour has been crossed LINE_COUNT times, start the stop sequence.
    if orange_count >= LINE_COUNT or blue_count >= LINE_COUNT:
        if not stop:
            stop_time = time.time()
        stop = True
    
    if stop:
        if(time.time() - stop_time > 1):  # short grace period before actually stopping
            print("Stopping")
            speed = 1022
            ser.write(f"1901022\n".encode())  # send the fixed stop command
            ser.flush()
            break


    if (SHOW_VID):
        # Overlay debug info (steering angle, line counts, FPS) on the preview frame.
        cv2.putText(cap, f"Steer: {steering:.2f}", (100, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
        cv2.putText(cap, f"O: {str(orange_count)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,127,255), 1)
        cv2.putText(cap, f"B: {str(blue_count)}", (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,127,0), 1)

        frame_count += 1
        elapsed = time.time() - frame_time
        if elapsed > 1.0:
            fps = frame_count // elapsed  # rough FPS sampled once per second
            frame_count = 0

            frame_time = time.time()
        cv2.putText(cap, f"FPS: {fps:.2f}", (220, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)            

        cv2.imshow("Video Frame", cap)


    ser.write(f"{steering}{speed}\n".encode())  # send steering+speed to the microcontroller each loop
    ser.flush()
    time.sleep(0.01)
    # print(f"sent value: heading: {steering} speed: {speed}")
    if cv2.waitKey(1) & 0xFF == ord('q'):  # manual quit key also sends the stop command
        ser.write(f"1901022\n".encode())
        ser.flush()
        break
ser.close()
        

cv2.destroyAllWindows()