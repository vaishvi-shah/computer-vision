import time
from picamera2 import Picamera2
import cv2

lowBlue = (100, 150, 0)
highBlue = (140, 255, 255)

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

time.sleep(2)  # Allow camera to warm up
while True:
    image = picam2.capture_array()
    # Define frame coordinates
    x1, y1, x2, y2 = 240, 140, 440, 340
    # Extract ROI
    roi = image[y1:y2, x1:x2]
    # Blur ROI
    blurred_roi = cv2.GaussianBlur(roi, (7, 7), 0)
    # Replace ROI in original image
    image[y1:y2, x1:x2] = blurred_roi
    
    #Come back to this
    # Detect blue contours within the ROI
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_roi, lowBlue, highBlue)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Draw contours on the ROI
    cv2.drawContours(image[y1:y2, x1:x2], contours, -1, (255, 0, 0), 2)

    
    # Draw frame
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 4)
    cv2.imshow("Captured Image", image)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cv2.destroyAllWindows()