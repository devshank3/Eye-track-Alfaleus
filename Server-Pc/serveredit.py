import io
import argparse
import socket
import struct
from PIL import Image
import cv2
import numpy as np
from skimage import img_as_bool
from skimage import img_as_ubyte
from skimage.morphology import skeletonize


# Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
# all interfaces)
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 8000))
server_socket.listen(0)



IMG_HEIGHT = 270
IMG_WIDTH = 480


def adjust_sharpness(imgIn):
    kernel = np.zeros((9, 9), np.float32)
    kernel[4, 4] = 2.0
    boxFilter = np.ones((9, 9), np.float32) / 81.0
    kernel = kernel - boxFilter
    custom = cv2.filter2D(imgIn, -1, kernel)
    return custom




# Accept a single connection and make a file-like object out of it
connection = server_socket.accept()[0].makefile('rb')
try:
    while True:
           # Read the length of the image as a 32-bit unsigned int. If the
           # length is zero, quit the loop
            image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
            if not image_len:
              break
            # Construct a stream to hold the image data and read the image
            # data from the connection
            image_stream = io.BytesIO()
            image_stream.write(connection.read(image_len))
            # Rewind the stream, open it as an image with PIL and do some
            # processing on it
            image_stream.seek(0)
            image = Image.open(image_stream)
            vs = np.array(image)
 
            a = 0
        
            a = a + 1
            #(grabbed, frame) = vs.read()

            

            frame = cv2.resize(vs, (IMG_WIDTH, IMG_HEIGHT))
            # print("[INFO] Resizing")
            M = np.ones(frame.shape, dtype="uint8") * 50
            added = cv2.add(frame, M)
            added = cv2.cvtColor(added, cv2.COLOR_BGR2GRAY)
            print("[INFO] Converted from RGB to GRAY for interation=", a)
            added = cv2.flip(added, 0)
            img = cv2.equalizeHist(added)
            # img = cv2.bilateralFilter(img, 20, 12, 12, cv2.BORDER_DEFAULT)
            img = cv2.medianBlur(img, 41)
            # img = cv2.GaussianBlur(img, (17, 17), 3, 3)
            # img = adjust_sharpness(img)
            img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 47, 6)
            img = cv2.GaussianBlur(img, (5, 5), 0, 0)
            rows, cols = img.shape

            pts3 = np.float32([[0, 0], [IMG_WIDTH, 0], [0, IMG_HEIGHT], [IMG_WIDTH, IMG_HEIGHT]])
            pts4 = np.float32(
            [[0, 0], [IMG_WIDTH, 0], [(IMG_WIDTH*0.14), IMG_HEIGHT], [(IMG_WIDTH*0.86), IMG_HEIGHT]])

            M = cv2.getPerspectiveTransform(pts3, pts4)

            img = cv2.warpPerspective(img,M,(IMG_WIDTH,IMG_HEIGHT))

            added = cv2.warpPerspective(added,M,(IMG_WIDTH,IMG_HEIGHT))
            # img = cv2.bitwise_not(img)
            img = img_as_bool(img)
            img = skeletonize(img)
            img = img_as_ubyte(img)
            circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1, minDist=1200000, param1=50, param2=6, minRadius=27, maxRadius=50)
            if circles is not None:
                  circles = np.round(circles[0, :]).astype("int")
                  for (x, y, r) in circles:
                          if x > (IMG_WIDTH * 0.3) and (IMG_HEIGHT * 0) < y < (IMG_HEIGHT * 1):
                              cv2.circle(added, (x, y), r, (255, 255, 255), 1)
                              cv2.rectangle(added, (x - 5, y - 5), (x + 5, y + 5), (255, 255, 255), 1)
                              print("[INFO] Computing for (", x, ",", y, ",", r, ")")
                              font = cv2.FONT_HERSHEY_SIMPLEX
                              cv2.putText(added, 'x:' + str(x), (20, 20), font, 0.6, (255, 255, 255), 1)
                              cv2.putText(added, 'y:' + str(y), (20, 40), font, 0.6, (255, 255, 255), 1)
                              cv2.putText(added, 'r:' + str(r), (20, 60), font, 0.6, (255, 255, 255), 1)
            # img = cv2.addWeighted(added, 1, img, 1, 1)
            cv2.imshow("img", img)
            cv2.imshow("Added", added)
            #cv2.imshow('Stream',cv_image)   
            if cv2.waitKey(1) & 0xFF == ord('q'):
               break
    
    

finally:
    connection.close()
    server_socket.close()
    vs.stop()
