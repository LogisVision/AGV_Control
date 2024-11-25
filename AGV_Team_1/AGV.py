from RecogWorkingArea import *
from RoadFollowing import *
from AutoMoveCamera import *
from jetbot import Robot
from SCSCtrl import TTLServo
from queue import Queue
from MyCamera import Camera
from enum import Enum
import threading
import time
import paho.mqtt.client as mqtt
import json
import threading

class Status(Enum):
    START = 'start'
    DONE = 'done'
    MOVING = 'moving'
    WORKING = 'working'
    WAITING = 'waiting'

class AGV():
    def __init__(self, robot_type):
        # 작업 큐 생성
        self.work_queue = Queue()

        self.robot_type = robot_type
        self.servo = AGVTeamOneServo() if robot_type == "A" else AGVTeamTwoServo()
        # self.servo.reset_degree()
        self.auto_move_camera = Tracking(robot_type)

        self.camera = Camera.instance()
        self.camera_lock = threading.Lock()

        self.auto_mode_active = False
        self.status = Status.WAITING

        self.incoming_area_color = 'green'
        self.common_work_space_color = 'yellow'

        self.th_streaming_flag = True
        self.motor_operate = False
        self.grap_finish = False

        # MQTT 클라이언트 설정
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.topics = {
            'sub_topic' : {
                'demon_status' : f'{self.robot_type}/Demon/Status/ToJetbot',
                'demon_command': f'{self.robot_type}/jetbot/command',
                'qt_calibrate_angle': f'{self.robot_type}/AGV/auto_mode',
                'qt_control': f'{self.robot_type}/AGV/control',
                'qt_command': f'{self.robot_type}/AGV/command',
                },
            'pub_topic' : {
                'demon_status' : f'{self.robot_type}/Demon/Status/ToDemon',
                'qt_streaming' : f'{self.robot_type}/AGV/camera',
                'qt_request_auto_mode' : f'{self.robot_type}/AGV/auto_mode_request',
            },
        }

        try:
            # 진이 핫스팟
            self.client.connect('172.20.10.9', 1883, 60)
            # 주원이형
            # self.client.connect('70.12.225.174', 1883, 60)
            # 철진님
            # self.client.connect('70.12.227.160', 1883, 60)
            self.client.loop_start()
        except Exception as e:
            print(f'MQTT 연결 중 오류 발생: {e}')
            self.cleanup_threads()

    def subscribe(self):
        try:
            for topic in self.topics['sub_topic'].values():
                self.client.subscribe(topic, 1)
                print(f'구독 {topic} !')
            print('구독 완료')
            return True
        except Exception as e:
            print(f'구독 중 오류 발생: {e}')
            self.cleanup()
            return False

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.servo.reset_degree()
            print('연결됨: '+str(rc))
        else:
            print('연결 실패: '+str(rc))

    def on_message(self, client, userdata, msg):
        try:
            # print(msg.topic, msg.payload)
            if msg.topic == self.topics['sub_topic']['demon_command']:
                # command = msg.payload.decode().strip().lower()
                command = json.loads(msg.payload.decode())
                """
                demon server msg sample
                B/Demon/Status/ToJetbot b'
                {"destination": {"address": "0", "state": "progress", "space": "workspaces"},
                "state": "completed",
                "robot": "B",
                "item": {"state": "progress", "id": "6c2jh4QkSw7NX7skPyY0", "location": {"address": "0", "state": "progress", "space": "incomings"}, "color": {"blue": 114, "green": 67, "red": 51}}}'
                """

                work_info = {
                    'destination': command['destination'],
                    'item': command['item']
                }
                
                self.work_queue.put(work_info)
                print(f"작업 추가됨: {work_info['item']} at {work_info['destination']}")
            
            elif msg.topic == self.topics['sub_topic']['demon_status']:
                # self.client.publish(self.topics['pub_topic']['demon_status'], self.status.value)
                self.client.publish(self.topics['pub_topic']['demon_status'], 'waiting')
                print(f'상태 전송 완료: {self.status.value}')

            elif msg.topic == self.topics['sub_topic']['qt_control']:
                command = msg.payload.decode("utf-8")
                print(command)
                if command == "AUTO_ON":
                    print("automode 시작")
                    self.auto_mode_active = True    
                        
                elif command == "AUTO_OFF":
                    self.auto_mode_active = False

            # 디버깅용
            elif msg.topic == self.topics['sub_topic']['qt_calibrate_angle']:
                if self.auto_mode_active and not self.motor_operate:
                    data = json.loads(msg.payload.decode("utf-8"))

                    self.auto_move_camera.offset_x = data.get("offset_x", self.auto_move_camera.mid_position_x)
                    self.auto_move_camera.offset_y = data.get("offset_y", self.auto_move_camera.mid_position_y)
                    self.auto_move_camera.distance = data.get("distance", 100)
                    self.auto_move_camera.box_angle = data.get("angle", 0)

                    self.motor_operate = True
                    self.camera_lock.acquire()
                    y = (2 / 9) * self.auto_move_camera.box_angle - 10
                    self.auto_move_camera.mid_position_x = 315 + y
                    self.auto_move_camera.tracking()    
                    self.camera_lock.release()

                    self.grap_finish = False
                    time.sleep(1)

                    if (
                        abs(self.auto_move_camera.offset_x - self.auto_move_camera.mid_position_x) <= self.auto_move_camera.th_x 
                    and abs(self.auto_move_camera.distance - self.auto_move_camera.th_distance) <= 1.0):
                        self.auto_mode_active = False
                        self.grap()
                        self.grap_finish = True
                    
                    self.motor_operate = False
                    

            elif msg.topic == self.topics['sub_topic']['qt_command'] and not self.auto_mode_active:
                if self.status == Status.WAITING:
                    self.handle_manual_commands(msg.payload.decode("utf-8"))
                else: 
                    print('작업 중에는 수동 제어를 할 수 없습니다.')

        except Exception as e:
            print(f'메시지 처리 중 오류 발생: {e}')
        
    def process_work(self):
        if self.status == Status.WAITING:
            try:
                # Queue에서 작업 가져오기 (작업이 없으면 대기)
                if not self.work_queue.empty():
                    work_info = self.work_queue.get(timeout=5)
                    print(f"새로운 작업 시작: {work_info['item']} at {work_info['destination']}")
                    
                    self.status = Status.START
                    self.start_threads(work_info)

                    # 작업 완료 표시
                    self.work_queue.task_done()
                    self.status = Status.DONE 
                    self.status = Status.WAITING
                pass

            except Exception as e:
                print(f'작업 처리 중 오류 발생: {e}')
                return

    def start_threads(self, work_info=None):
        print('박스 잡기 시작!')
        self.move_and_grap(work_info)
        print('박스 잡기 완료!')

        time.sleep(1)

        print('박스 놓기 시작!')
        self.move_and_drop(work_info)
        print('박스 놓기 완료!')
        

    def move_and_grap(self, work_info):
        # TODO : Requires Test
        # TODO : Define specific work

        self.status = Status.MOVING 
        
        target_color = 'green' if self.robot_type == "A" else 'yellow'
        print(f'작업대 색상: {target_color}')
        
        self.execute_road_following(target_color)
        # stop_event = threading.Event()
        # stop_event.clear()
        # # 새로운 쓰레드 객체 생성
        # self.recog_working_area = RecogWorkingArea(self.robot_type, stop_event)
        # self.road_following = RoadFollowing(self.robot_type, stop_event)
        # self.recog_working_area.working_area = [target_color]
        # print(self.recog_working_area.working_area)

        # # 쓰레드 시작
        # self.recog_working_area.start()
        # self.road_following.start()

        # # # 이벤트 대기
        # while not stop_event.is_set():
        #     time.sleep(0.1)

        # # 쓰레드 정리
        # self.cleanup_threads()

        print(f'작업대 도착 완료!')

        self.status = Status.WORKING
        
        self.calibrate_position(1)
        # self.calibrate_position(work_info['item']['location']['address'])
        self.servo.robot_speed = 0.5
        self.servo.move_duration = 2.5
        self.servo.move("r")
        time.sleep(1)
        self.servo.move_duration = 1.0
        self.servo.move("b")
        self.servo.operate_arm(5, 0)

        self.servo.reset_speed()
        
        # 로봇 동작
        # TODO: 박스 잡기 작업 수행
        print('박스 잡기 시작!')
        data = {'auto_mode' : 'Start'}
        self.client.publish(self.topics['pub_topic']['qt_request_auto_mode'], json.dumps(data))

        self.grap_finish = False
        
        while not self.grap_finish:
            time.sleep(0.1)
        
        self.grap_finish = False

        self.servo.robot_speed = 0.5
        self.servo.move_duration = 1.0
        self.servo.move("b")
        time.sleep(1)
        self.servo.move_duration = 2.5
        self.servo.move("l")
        print('박스 잡기 완료!')

    def move_and_drop(self, work_info):
        self.status = Status.MOVING
        target_color = 'yellow' if self.robot_type == "A" else 'green'
        print(f'목표 위치 색상: {target_color}')
        self.execute_road_following(target_color)
        print(f'목표 위치 도착 완료!')

        self.status = Status.WORKING

        # 로봇 동작
        # TODO: 박스 놓기 작업 수행 
        self.calibrate_position(1)
        # self.calibrate_position(work_info['destination']['address'])

        self.servo.robot_speed = 0.5
        self.servo.move_duration = 2.5
        self.servo.move("r")
        self.drop()

        # TTLServo.servoAngleCtrl(2, 55, 1, 165)
        # TTLServo.servoAngleCtrl(3, 55, 1, 180)
        # time.sleep(4)
        # # 그랩 놓기
        # TTLServo.servoAngleCtrl(4, 0, 1, 150)
        # time.sleep(3)
        # TTLServo.servoAngleCtrl(3,-40, 1, 190) # 팔빼기
        # TTLServo.servoAngleCtrl(2, 20, 1, 160)
        # time.sleep(2)
        # TTLServo.xyInputSmooth(80, 80,2) # 초기상태

        # self.servo.move("l")
        self.servo.reset_speed()

    def execute_road_following(self, target_color):
        stop_event = threading.Event()
        stop_event.clear()
        # 새로운 쓰레드 객체 생성
        self.recog_working_area = RecogWorkingArea(self.robot_type, stop_event)
        self.road_following = RoadFollowing(self.robot_type, stop_event)
        self.recog_working_area.working_area = [target_color]
        
        # 쓰레드 시작
        self.recog_working_area.start()
        self.road_following.start()

        # # 이벤트 대기
        while not stop_event.is_set():
            time.sleep(0.1)

        # 쓰레드 정리
        self.cleanup_threads()

    def calibrate_position(self, idx):
        if idx == 1:
            return
        self.servo.move_duration = 1
        self.servo.robot_speed = 0.5
        if idx == 2:
            self.servo.move("f")
        elif idx == 0:
            self.servo.move("b")

    def send_frame(self):
        while self.th_streaming_flag:
            if not self.motor_operate:
                _, buffer = cv2.imencode('.jpg', self.camera.ori_value, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                jpg_as_text = buffer.tobytes()
                self.client.publish(self.topics['pub_topic']['qt_streaming'], jpg_as_text)
                time.sleep(0.5)
                

    def stop_send_frame(self):
        self.th_streaming_flag = False

    def handle_manual_commands(self, payload):
        try:
            message = json.loads(payload)
            command = message.get("cmd_string", "")
            arg = message.get("arg_string", 0)

            if isinstance(arg, str) and ',' in arg:
                x, y = map(int, arg.split(','))
            else:
                arg = int(float(arg)) if isinstance(arg, str) and '.' in arg else int(arg)

            if command == "go":
                self.servo.move("f")
            elif command == "back":
                self.servo.move("b")
            elif command == "mid":
                self.servo.stop()
            elif command == "left":
                self.servo.move("l")
            elif command == "right":
                self.servo.move("r")
            elif command == "grab_angle":
                self.servo.operate_arm(4, int(arg))
            elif command == "camera_angle":
                self.servo.operate_arm(5, int(arg))
            elif command == "camera_turn_angle":
                self.servo.operate_arm(1, int(arg))
            elif command == "move_arms":
                x, y = map(int, int(arg).split(","))
                x = max(85, min(x, 200))
                y = max(-50, min(y, 100))
                TTLServo.xyInput(x, y)
            elif command == "arm_x":
                self.servo.operate_arm(2, int(arg))
            elif command == "arm_y":
                self.servo.operate_arm(3, int(arg))
            elif command == "reset":
                self.servo.reset_degree()
        except Exception as e:
            print("Error processing manual command:", e)

    def cleanup_threads(self):
        try:
            self.recog_working_area.stop()
            self.recog_working_area.join()
            self.road_following.stop()
            self.road_following.join()
        except Exception as e:
            print(f'정리 중 오류 발생: {e}')

    def terminate(self):
        self.cleanup_threads()
        self.servo.stop()
        self.client.loop_stop()
        self.client.disconnect()

    def grap(self):
        TTLServo.xyInputSmooth(242,-40, 2)
        # Gripper 동작
        time.sleep(3)
        TTLServo.servoAngleCtrl(4, -36, 1, 150)
        time.sleep(3)
        TTLServo.xyInputSmooth(80, 80,2)
        time.sleep(3)

    def drop(self):
        TTLServo.xyInputSmooth(242,-40, 2)
        time.sleep(3)
        TTLServo.servoAngleCtrl(4, 80, 1, 150)
        time.sleep(3)
        TTLServo.xyInputSmooth(80, 80,2)
        time.sleep(3)


if __name__ == '__main__':
    try:
        agv = AGV("B")
        agv.subscribe()
        streaming_thread = threading.Thread(target=agv.send_frame, daemon=True)
        streaming_thread.start()
        agv.start_threads()
        while True:
            # agv.process_work()
            time.sleep(1)
    except KeyboardInterrupt:
        agv.terminate() 

