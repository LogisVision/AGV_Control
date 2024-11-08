from ArmServo import *
import threading

class Tracking(threading.Thread):
    def __init__(self, robot_type):
        self.servo = AGVTeamOneServo() if robot_type == "A" else AGVTeamTwoServo()
        self.robot_type = robot_type
        self.threshold_x = 0
        self.threshold_y = 0
        self.offset_x = 0
        self.offset_y = 0
        self.th_flag = True

    def tracking(self):
        # 좌우 (turnAngle) 조정
        if self.offset_x < -self.threshold_x:  # 화면 중심보다 왼쪽에 있을 때
            self.servo.operate_arm(1, self.servo.motor_degree[1] - 3)
            
        elif self.offset_x > self.threshold_x:  # 화면 중심보다 오른쪽에 있을 때
            self.servo.operate_arm(1, self.servo.motor_degree[1] + 3)
            
        print(f"Turn angle adjusted to: {self.servo.motor_degree[1]}")

        # 상하 (camAngle) 조정
        if self.offset_y < -self.threshold_y:  # 화면 중심보다 위쪽에 있을 때
            self.servo.operate_arm(5, self.servo.motor_degree[5] - 3)
        
        elif self.offset_y > self.threshold_y:  # 화면 중심보다 아래쪽에 있을 때
            self.servo.operate_arm(5, self.servo.motor_degree[5] + 3)
        
        print(f"Camera angle adjusted to: {self.servo.motor_degree[5]}")

    def run(self):
        while self.th_flag:
            self.tracking()
            time.sleep(0.1)
    
    def stop(self):
        self.th_flag = False
