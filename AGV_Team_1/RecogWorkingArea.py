import threading
import cv2
import time
import numpy as np
from MyCamera import Camera
from ArmServo import *
from traitlets.config.configurable import Config  

class RecogWorkingArea(threading.Thread):
    def __init__(self, robot_type, stop_event):
        super().__init__()
        self.working_areas = ['yellow']
        self.is_find_color = False
        self.robot_type = robot_type
        # Colors HSV range
        # index 0 : lower range
        # index 1 : upper range
        # Todo: Get Color Range
        self.colors_range = {
            # 'red' : [np.array([2, 155, 170]), np.array([12, 175, 200])],
            # 'green' : [np.array([60, 120, 160]), np.array([80, 150, 180])],
            # 'blue' : [np.array([100, 130, 150]), np.array([140, 255, 190])],
            # 'yellow' : [np.array([24, 50, 160]), np.array([32, 255, 220])],
            # 'orange' : [np.array([12, 125,200]), np.array([20, 240, 220])],
            # 'purple' : [np.array([110, 100, 140]), np.array([140, 140, 170])],
            'red' : [np.array([15, 120, 178]), np.array([36, 140, 200])],
            'green' : [np.array([70, 145, 155]), np.array([80, 150, 170])],
            'blue' : [np.array([100, 140, 180]), np.array([120, 160, 210])],
            'yellow' : [np.array([26, 130, 180]), np.array([30, 160, 220])],
            'orange' : [np.array([15, 170,170]), np.array([18, 200, 200])],
            'purple' : [np.array([110, 125, 140]), np.array([140, 145, 180])],
        }

        self.camera = Camera.instance()

        self.servo = AGVTeamOneServo() if robot_type == "A" else AGVTeamTwoServo()
        self.servo.operate_arm(5, 55)

        self.frame_width = self.camera.width
        self.frame_height = self.camera.height

        self.camera_center_x = int(self.frame_width/2)
        self.camera_center_y = int(self.frame_height/2)

        # Validation data set length
        self.max_len = 20
        self.color_hsv_value_list = []

        self.th_flag = True
        self.imageInput = 0

        self.stop_event = stop_event

    def run(self):
        self.find_time = None
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
                    error_Y, error_X = self.colorAction(Contours)
                    print(error_X)
                    if error_X < 150:
                        self.find_time = time.time()
                        self.is_find_color = True
                        # self.colorAction(Contours)
                    break

                time.sleep(0.1)

                # 1초 안에 색 못 찾으면 event 발생
                if self.find_time is not None and time.time() - self.find_time > 1:
                    self.stop_event.set()
                    print("1초 안에 색 못 찾음")
                    break
                
                self.is_find_color = False
                

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

        return [error_Y, error_X]

        # self.is_find_color = True

    def stop(self):
        self.th_flag = False
        self.servo.stop()
        # self.camera.stop()
