import torchvision.transforms as transforms
import torch.nn.functional as F
import PIL.Image
import numpy as np
import threading
from MyCamera import Camera
from ArmServo import *
from SteeringModel import *

class RoadFollowing(threading.Thread):
    def __init__(self, robot_type, stop_event):
        super().__init__()
        self.steering_model = SteeringModel()

        # Peripheral
        self.camera = Camera.instance()
        self.robot_type = robot_type
        self.servo = AGVTeamOneServo() if robot_type == "A" else AGVTeamTwoServo()
        # Camera angle should be set with data collection environment
        self.servo.operate_arm(5, -55)

        # Parameter for road following
        self.speed_gain = 0.3
        # Steering Coefficient
        self.steering_gain = 0.2
        # Differential Steering Coefficient
        self.steering_dgain = 0.2
        self.steering_bias = 0.0

        # Angle for Turn
        self.angle = 0.0
        self.angle_last = 0.0

        # Road Following Execute Flag
        self.th_flag = True
        self.stop_event = stop_event
    def preprocess(self, image):
        image = PIL.Image.fromarray(image)
        image = transforms.functional.to_tensor(image).to(self.steering_model.device).half()
        image.sub_(self.steering_model.mean[:, None, None]).div_(self.steering_model.std[:, None, None])
        return image[None, ...]

    def run(self):
        self.execute_road_following()

    def execute_road_following(self):
        while self.th_flag and not self.stop_event.is_set():
            image = self.camera.value
            xy = self.steering_model.model(self.preprocess(image)).detach().float().cpu().numpy().flatten()
            x = xy[0]
            y = (0.5 - xy[1]) / 2.0

            # 조향값 계산
            self.angle = np.arctan2(x, y)

            # PID 제어를 이용한 모터 제어
            pid = self.angle * self.steering_gain + (self.angle - self.angle_last) * self.steering_dgain
            self.angle_last = self.angle

            steering_value = pid + self.steering_bias

            self.servo.robot.left_motor.value = max(min(self.speed_gain + steering_value, 1.0), 0.0)
            self.servo.robot.right_motor.value = max(min(self.speed_gain - steering_value, 1.0), 0.0)
        self.servo.stop()

    def stop(self):
        self.th_flag = False