from SCSCtrl import TTLServo
from jetbot import Robot
import time

class AGVServo:
    _instance = None  # 싱글톤 인스턴스를 저장하는 클래스 변수

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AGVServo, cls).__new__(cls)
        return cls._instance

    def __init__(self, init_degree = [-1, 0, 0, 0, 0, 0]):
        # 이미 초기화된 경우, 다시 초기화하지 않음
        if hasattr(self, '_initialized') and self._initialized:
            return
        self.speed_motor = 150
        self.dir = 1
        self.motor_degree = init_degree.copy()
        self.sensitivity_degree = 5
        self.robot = Robot()
        for i in range(1, 6):
            TTLServo.servoAngleCtrl(i, self.motor_degree[i], self.dir, self.speed_motor)
        self.robot.stop()
        self.robot_speed = 0.1
        self.move_duration = 0.5
        self.initial_degree = init_degree
        self._initialized = True  # 초기화 상태를 기록하여 중복 초기화 방지

    def reset_speed(self):
        self.robot_speed = 0.1
        self.move_duration = 0.5

    def check_in_range(self, idx, degree):
        if idx == 5:
            if degree > 80:
                return 80
            if degree < -50:
                return -50
        else:
            if degree > 150:
                return 150
            if degree < -150:
                return -150
        return degree

    def update_degree(self, idx, degree):
        self.motor_degree[idx] = self.check_in_range(idx, degree)

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
            return
        self.update_degree(idx, degree)
        TTLServo.servoAngleCtrl(
            idx,
            self.motor_degree[idx],
            self.dir,
            self.speed_motor
        )

    def reset_degree(self):
        for idx, deg in enumerate(self.initial_degree):
            if idx > 0:  # idx 0은 더미값(-1)이므로 건너뜁니다
                self.operate_arm(idx, deg)
            
    def stop(self):
        self.robot.stop()

    def move(self, direction):
        if direction == "f" or direction == "F":
            self.robot.forward(self.robot_speed)
        elif direction == "b" or direction == "B":
            self.robot.backward(self.robot_speed)
        elif direction == "r" or direction == "R":
            self.robot.right(self.robot_speed)
        elif direction == "l" or direction == "L":
            self.robot.left(self.robot_speed)

        time.sleep(self.move_duration)
        self.stop()

    def __del__(self):
        self.robot.stop()


# 싱글톤 기반의 AGVTeamOneServo 클래스
class AGVTeamOneServo(AGVServo):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AGVTeamOneServo, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.initial_degree = [-1, 8, 0, 0, 0, 0]
        super().__init__(self.initial_degree)


# 싱글톤 기반의 AGVTeamTwoServo 클래스
class AGVTeamTwoServo(AGVServo):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AGVTeamTwoServo, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # 하드 코딩 시
        # 맵으로부터 작업대가 37cm, 작업대 오른쪽으로부터 박스가 27cm
        
        self.initial_degree = [-1, -6, -11, -7, 0, -4]
        self.grap_box_degree = [-1, -6, 73, 60, 0, -4]
        self.grap_degree = -27
        super().__init__(self.initial_degree)
