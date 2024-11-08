from SCSCtrl import TTLServo
from jetbot import Robot
import time

class AGVServo:
    def __init__(self, init_degree):
        self.speed_motor = 150
        self.dir = -1
        self.motor_degree = init_degree
        self.sensitivity_degree = 5
        self.robot = Robot()
        for i in range(1, 6):
            TTLServo.servoAngleCtrl(i, self.motor_degree[i], self.dir, self.speed_motor)
        self.robot.stop()

    def check_in_range(self, degree):
        if degree > 150:
            return 150
        if degree < -150:
            return -150
        return degree

    def update_degree(self, idx, degree):
        self.motor_degree[idx] = self.check_in_range(degree)

    """
    idx meaning
    1 : horizontal arm
    2 : vertical arm 1
    3 : vertical arm 2
    4 : Grip
    5 : Camera
    """
    def operate_arm(self, idx, degree):
        if idx < 1 or idx > 5:
            pass
        self.update_degree(idx, degree)
        TTLServo.servoAngleCtrl(
            idx,
            self.motor_degree[idx],
            self.dir,
            self.speed_motor
        )

    def stop(self):
        self.robot.stop()

    def move(self, direction, speed, duration):
        if direction == "f" or direction == "F":
            self.robot.forward(speed)
        elif direction == "b" or direction == "B":
            self.robot.backward(speed)
        elif direction == "r" or direction == "R":
            self.robot.right(speed)
        elif direction == "l" or direction == "L":
            self.robot.left(speed)

        time.sleep(duration)
        self.stop()

class AGVTeamOneServo(AGVServo):
    def __init__(self):
        super().__init__([-1, 8, 0, 0, 0, 0])

class AGVTeamTwoServo(AGVServo):
    def __init__(self):
        super().__init__([-1, 6, 11, 7, 0, 4])

