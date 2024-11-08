from jetbot import Robot, bgr8_to_jpeg
from ArmServo import AGVTeamTwoServo

import threading
import numpy as np
import paho.mqtt.client as mqtt
from datetime import datetime
import pytz
import time
import json
import random as rd

addr = ""
port = "1883"

class MQTTClient:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.topics = {
            "cameraTopic" : "AGV/camera",
            "commandTopic" : "AGV/command",
            "sensingTopic" : "AGV/sensing",
        }
        self.kr_timezone = pytz.timezone("Asia/Seoul")
        self.client = mqtt.Client()

        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("connected OK")
        else:
            print("Bad connection Returned code=", rc)

    def on_publish(self, client, userdata, result):
        print("data published")

    def on_message(self, client, userdata, msg):
        global message
        message = json.loads(msg.payload.decode("utf-8"))
        print(message, type(message))

        commandlbl.value = message["cmd_string"]
        # TODO: Link AGVServo's Function
        if message["cmd_string"] == "go":
            agv_forward()
        elif message["cmd_string"] == "mid":
            agv_stop()
        elif message["cmd_string"] == "left":
            agv_left()
        elif message["cmd_string"] == "right":
            agv_right()
        elif message["cmd_string"] == "back":
            agv_backward()
        elif message["cmd_string"] == "camera_angle":
            camAngle(message["arg_string"])
        elif message["cmd_string"] == "camera_turn_angle":
            turnAngle(message["arg_string"])
        elif message["cmd_string"] == "grab_angle":
            grab(message["arg_string"])
        elif message["cmd_string"] == "arm1":
            arm1(message["arg_string"])
            # print(message["arg_string"])
        elif message["cmd_string"] == "arm2":
            arm2(message["arg_string"])
            # print(message["arg_string"])
        elif message["cmd_string"] == "stop":
            print('stop')
        elif message["cmd_string"] == "exit":
            print('exit')
            publishingData.stop()
            agv_stop()

    def subscribe(self, topic, qos=1):
        self.client.subscribe(topic, qos)

    def publish(self, topic, data, qos=1):
        self.client.publish(topic, data, qos)

    # TODO
    # Streaming
    # Object Detection

if __name__ == '__main__':
    global addr, port
    servo = AGVTeamTwoServo()
    client = MQTTClient(addr, port)
    client.subscribe(client.topics["commandTopic"])

