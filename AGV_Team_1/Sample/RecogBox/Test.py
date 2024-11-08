import torchvision
import torch
import torchvision.transforms as transforms
import torch.nn.functional as F
import cv2
import PIL.Image
import numpy as np
import time
from jetbot import Camera
from jetbot import Robot
from ArmServo import *

def preprocess(image):
    image = PIL.Image.fromarray(image)
    image = transforms.functional.to_tensor(image).to(device).half()
    image.sub_(mean[:, None, None]).div_(std[:, None, None])
    return image[None, ...]

model = torchvision.models.resnet18(pretrained=False)
model.fc = torch.nn.Linear(512, 2)
model.load_state_dict(torch.load('best_box_recog_model.pth')) 

device = torch.device('cuda')
model = model.to(device)
#.half() : 부동소수점 형식을 16비트로 낮춰서 메모리 사용량을 줄이고 연산 속도를 높인다.
model = model.eval().half()

mean = torch.Tensor([0.485, 0.456, 0.406]).cuda().half()
std = torch.Tensor([0.229, 0.224, 0.225]).cuda().half()

camera = Camera.instance()

robot = Robot()

angle = 0.0
angle_last = 0.0

servo = AGVTeamTwoServo()
servo.reset_degree()

print("start")

while True:
    image = camera.value
    xy = model(preprocess(image)).detach().float().cpu().numpy().flatten()
    x = xy[0]
    y = (0.5 - xy[1]) / 2.0

    cur_degree = servo.motor_degree[1]
    print(x, y, cur_degree)
    if x > 0.05:
        cur_degree -= 1
        if cur_degree < -150:
            cur_degree = -150
    elif x < -0.05:
        cur_degree += 1
        if cur_degree > 150:
            cur_degree = 150
    servo.operate_arm(1, cur_degree)
    
    # time.sleep(0.5)
    #조향값 계산
    # angle = np.arctan2(x, y)
    
    # #PID 제어를 이용한 모터 제어
    # pid = angle * steering_gain_slider.value + (angle - angle_last) * steering_dgain_slider.value
    # angle_last = angle
    
    # steering_slider.value = pid + steering_bias_slider.value
    
    # robot.left_motor.value = max(min(speed_slider.value + steering_slider.value, 1.0), 0.0)
    # robot.right_motor.value = max(min(speed_slider.value - steering_slider.value, 1.0), 0.0)
    
# execute({'new': camera.value})