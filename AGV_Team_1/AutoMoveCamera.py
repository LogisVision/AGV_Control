from ArmServo import *
import threading

class Tracking(threading.Thread):
    def __init__(self, robot_type):
        super().__init__()
        
        self.servo = AGVTeamOneServo() if robot_type == "A" else AGVTeamTwoServo()
        self.robot_type = robot_type
        self.th_x = 2
        self.th_y = 2
        self.offset_x = 0
        self.offset_y = 0
        self.th_flag = True
        self.th_distance = 20
        self.mid_position_x = 320
        self.mid_position_y = 240
        self.distance = 100

    def tracking(self):
        if abs(self.distance - self.th_distance) > 10:
            self.servo.speed_motor = 0.2
        else:
            self.servo.speed_motor = 0.1
            
        if self.distance - self.th_distance > 1:
            self.servo.move("f")
        elif self.distance - self.th_distance < -1:
            self.servo.move("b")

        # 좌우 (turnAngle) 조정
        if self.offset_x - self.mid_position_x < -1 * self.th_x :  # 화면 중심보다 왼쪽에 있을 때
            self.servo.operate_arm(1, self.servo.motor_degree[1] - 1)
            
        elif self.offset_x - self.mid_position_x > self.th_x :  # 화면 중심보다 오른쪽에 있을 때
            self.servo.operate_arm(1, self.servo.motor_degree[1] + 1)

        # print(f"Turn angle adjusted to: {self.servo.motor_degree[1]}")

        # 상하 (camAngle) 조정
        if self.offset_y - self.mid_position_y < -1 * self.th_y :  # 화면 중심보다 위쪽에 있을 때
            self.servo.operate_arm(5, self.servo.motor_degree[5] - 1)

        elif self.offset_y - self.mid_position_y > 1 * self.th_y :  # 화면 중심보다 아래쪽에 있을 때
            self.servo.operate_arm(5, self.servo.motor_degree[5] + 1)

        # print(f"Camera angle adjusted to: {self.servo.motor_degree[5]}")

    def run(self):
        while self.th_flag:
            self.tracking()
            time.sleep(0.1)
    
    def stop(self):
        self.th_flag = False
