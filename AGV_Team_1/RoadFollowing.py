import torchvision
import torch
import torchvision.transforms as transforms
import torch.nn.functional as F
import PIL.Image
import numpy as np
import threading
from MyCamera import Camera
from ArmServo import *

class RoadFollowing(threading.Thread):
    def __init__(self, idx, stop_event):
        super().__init__()
        # Model Variable
        self.model = torchvision.models.resnet18(pretrained=True)
        self.model.fc = torch.nn.Linear(512, 2)
        self.model.load_state_dict(torch.load('best_steering_model_xy_test (2).pth'))

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self.model.to(self.device)
        self.model = self.model.eval().half()

        self.mean = torch.Tensor([0.485, 0.456, 0.406]).cuda().half()
        self.std = torch.Tensor([0.229, 0.224, 0.225]).cuda().half()

        # Peripheral
        self.camera = Camera.instance()
        self.servo = AGVTeamOneServo() if idx == 1 else AGVTeamTwoServo()
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
        image = transforms.functional.to_tensor(image).to(self.device).half()
        image.sub_(self.mean[:, None, None]).div_(self.std[:, None, None])
        return image[None, ...]

    def run(self):
        self.execute_road_following()

    def execute_road_following(self):
        while self.th_flag and not self.stop_event.is_set():
            image = self.camera.value
            xy = self.model(self.preprocess(image)).detach().float().cpu().numpy().flatten()
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