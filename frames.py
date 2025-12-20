import cv2

class Frame:
    def __init__(self, img, x1,x2,y1,y2,low,high):
        self.img = img
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.low = low
        self.high = high
        
        self.frame = 0
        self.mask = 0
        self.hsv = 0
        self.frame_gaussed = 0
        self.contours = 0

        self.update(img)

    def update(self, img):
        cv2.rectangle(img, (self.x1,self.y1), (self.x2,self.y2), (255, 255, 255), 1)
        self.frame = img[self.y1:self.y2, self.x1:self.x2]
        self.frame_gaussed = cv2.GaussianBlur(self.frame, (1, 1), cv2.BORDER_DEFAULT)  # blurring the image
        self.hsv = cv2.cvtColor(self.frame_gaussed, cv2.COLOR_BGR2HSV)


    def find_contours(self, is_red=False):
        self.mask = cv2.inRange(self.hsv, self.low[0], self.high[0])        
        if is_red:
            mask1 = cv2.inRange(self.hsv, self.low[1], self.low[1])
            self.mask = cv2.bitwise_or(self.mask, mask1)
        
        contours, _ = cv2.findContours(self.mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        if contours:
            cv2.drawContours(self.frame, contours, -1, (0, 0, 255), 2)
