import threading
import cv2
import time
import numpy as np
from MyCamera import Camera
from ArmServo import *

class RecogWorkingArea(threading.Thread):
    def __init__(self, idx):
        super().__init__()
        self.working_areas = ['red', 'blue']
        # Colors HSV range
        # index 0 : lower range
        # index 1 : upper range
        # Todo: Get Color Range
        self.colors_range = {
            'red' : [np.array([0, 0, 0]), np.array([0, 0, 0])],
            'green' : [np.array([0, 0, 0]), np.array([0, 0, 0])],
            'blue' : [np.array([0, 0, 0]), np.array([0, 0, 0])],
            'yellow' : [np.array([0, 0, 0]), np.array([0, 0, 0])],
        }

        self.camera = Camera.instance()
        self.servo = AGVTeamOneServo() if idx == 1 else AGVTeamTwoServo()

        self.frame_width = self.camera.width
        self.frame_height = self.camera.height

        self.camera_center_x = int(self.frame_width/2)
        self.camera_center_y = int(self.frame_height/2)

        # Validation data set length
        self.max_len = 20
        self.color_hsv_value_list = []

        self.th_flag = True
        self.imageInput = 0

    def run(self):
        while self.th_flag:
            self.imageInput = self.camera.value
            hsv = cv2.cvtColor(self.imageInput, cv2.COLOR_BGR2HSV)

            # blur
            hsv = cv2.blur(hsv, (15, 15))

            # Compare current hsv and color hsv value range
            for color in self.working_areas:
                mask = cv2.inRange(hsv, self.colors_range[color][0], self.colors_range[color][1])

                # Erase Noise
                mask = cv2.erode(mask, None, iterations=2)
                mask = cv2.dilate(mask, None, iterations=2)

                # Get Outline
                Contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                if Contours:
                    self.colorAction(Contours)
                    break

                time.sleep(0.1)

    def colorAction(self, Contours):
        # Find Biggest Area about Working area
        c = max(Contours, key=cv2.contourArea)
        ((box_x, box_y), radius) = cv2.minEnclosingCircle(c)

        # Biggest Working Area Point
        X = int(box_x)
        Y = int(box_y)

        # Distance between working area outline and camera center
        error_Y = abs(self.camera_center_y - Y)
        error_X = abs(self.camera_center_x - X)

        # Todo: Define Action

    def stop(self):
        self.th_flag = False
        self.servo.stop()
