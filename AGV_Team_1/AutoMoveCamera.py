from ArmServo import *
import threading

class Tracking(threading.Thread):
    def __init__(self, idx):
        self.servo = AGVTeamOneServo() if idx == 1 else AGVTeamTwoServo()
        self.threshold_x = 0
        self.threshold_y = 0

    def tracking(self, offset_x, offset_y):
        # 좌우 (turnAngle) 조정
        if offset_x < -self.threshold_x:  # 화면 중심보다 왼쪽에 있을 때
            self.servo.operate_arm(1, self.servo.motor_degree[1] - 3)
            
        elif offset_x > self.threshold_x:  # 화면 중심보다 오른쪽에 있을 때
            self.servo.operate_arm(1, self.servo.motor_degree[1] + 3)
            
        print(f"Turn angle adjusted to: {self.servo.motor_degree[1]}")

        # 상하 (camAngle) 조정
        if offset_y < -self.threshold_y:  # 화면 중심보다 위쪽에 있을 때
            self.servo.operate_arm(5, self.servo.motor_degree[5] - 3)
        
        elif offset_y > self.threshold_y:  # 화면 중심보다 아래쪽에 있을 때
            self.servo.operate_arm(5, self.servo.motor_degree[5] + 3)
        
        print(f"Camera angle adjusted to: {self.servo.motor_degree[5]}")
