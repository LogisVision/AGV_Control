from RecogWorkingArea import *
from RoadFollowing import *
from AutoMoveCamera import *
from jetbot import Robot
from SCSCtrl import TTLServo
from queue import Queue
from MyCamera import Camera
import time
import paho.mqtt.client as mqtt
import json
import threading

# class WorkType:
#     PICKUP = 'pickup'
#     DROPOFF = 'dropoff'
    
    # @classmethod
    # def is_valid(cls, command: str) -> bool:
    #     command_type = command.split(',')[0]
    #     return command_type in [cls.PICKUP, cls.DROPOFF]

class Status:
    MOVING = 'moving'
    WORKING = 'working'
    WAITING = 'waiting'

class AGV():
    def __init__(self, robot_type):
        self.idx = idx

        # 작업 큐 생성
        self.work_queue = Queue()
        self.robot_type = robot_type

        self.robot_type = robot_type
        self.servo = AGVTeamOneServo() if robot_type == "A" else AGVTeamTwoServo()
        self.servo.reset_degree()

        self.camera = Camera.instance()

        self.auto_mode_active = False
        self.status = Status.WAITING

        self.th_streaming_flag = True

        # MQTT 클라이언트 설정
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.topics = {
            'sub_topic' : {
                'demon_command': f'{self.idx}/jetbot/command',
                'auto_mode': f'{self.idx}/AGV/auto_mode',
                'qt_control': f'{self.idx}/AGV/control',
                'qt_command': f'{self.idx}/AGV/command'
                },
            'pub_topic' : {
                'qt_streaming' : f'{self.idx}/AGV/camera'
            },
        }

        try:
            self.client.connect('70.12.225.174', 1883, 60)
            self.client.loop_start()
        except Exception as e:
            print(f'MQTT 연결 중 오류 발생: {e}')
            self.cleanup()

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
            print(msg.topic, msg.payload)
            if msg.topic == self.topics['sub_topic']['demon_command']:
                command = msg.payload.decode().strip().lower()
                # if WorkType.is_valid(command):
                # 명령어를 타입과 위치로 분리
                # parts = command.split()
                # work_type = parts[0]
                # workspace = parts[1] if len(parts) > 1 else None
                if 

                work_info = {
                    'destination': command['destination'],
                    'item': command['item']
                }
                
                self.work_queue.put(work_info)
                print(f'작업 추가됨: {work_type} at {workspace}')
                # else:
                #     print(f'잘못된 작업 타입: {command}')

            elif msg.topic == self.topics['sub_topic']['qt_control']:
                command = msg.payload.decode("utf-8")
                if command == "AUTO_ON":
                    self.auto_mode_active = True
                    self.auto_move_camera = Tracking(self.idx)
                    self.auto_move_camera.start()
                        
                elif command == "AUTO_OFF":
                    self.auto_mode_active = False
                    self.auto_move_camera.stop()
                    self.auto_move_camera.join()
            
            # 디버깅용
            elif msg.topic == self.topics['sub_topic']['auto_mode']:
                if self.auto_mode_active:
                    data = json.loads(msg.payload.decode("utf-8"))
                    self.auto_move_camera.offset_x = data.get("offset_x", 0)
                    self.auto_move_camera.offset_y = data.get("offset_y", 0)

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
                work_info = self.work_queue.get(timeout=5)
                work_type = work_info['type']
                workspace = work_info['workspace']
                print(f'새로운 작업 시작: {work_type} at {workspace}')
                
                self.start_threads(work_info)
                
                # 작업 완료 표시
                self.work_queue.task_done()
            except self.work_queue.Empty:
                print('작업 큐가 비어있습니다.')
                return
            except Exception as e:
                print(f'작업 처리 중 오류 발생: {e}')
                return

    def start_threads(self, work_info):
        # TODO : Requires Test
        # TODO : Define specific work

        self.status = Status.MOVING 

        stop_event = threading.Event()
        current_color = work_info['workspace']
        current_work_type = work_info['type']
        
        # 새로운 쓰레드 객체 생성
        self.recog_working_area = RecogWorkingArea(self.idx, stop_event)
        self.road_following = RoadFollowing(self.idx, stop_event)

        # 현재 찾을 색상 설정
        self.recog_working_area.working_areas = [current_color]
        print(f'찾고있는 색상: {current_color}')

        # 쓰레드 시작
        self.recog_working_area.start()
        self.road_following.start()

        # 이벤트 대기
        while not stop_event.is_set():
            time.sleep(0.1)

        print(f'{current_color} 감지됨!')
        
        # 쓰레드 정리
        self.cleanup_threads()
        
        self.status = Status.WORKING

        # 로봇 동작
        # 작업 타입에 따라서 다른 동작 수행
        if current_work_type == 'pickup':
            # TODO 픽업 동작 추가
            print('픽업 중...')
        elif current_work_type == 'dropoff':
            # TODO 놓기 동작 추기
            print('물건을 자리에 놓는 중...')

    def send_frame(self):
        while self.th_streaming_flag:
            _, buffer = cv2.imencode('.jpg', self.camera.value, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
            jpg_as_text = buffer.tobytes()
            self.client.publish(self.topics['pub_topic']['qt_streaming'], jpg_as_text)
            

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
                self.servo.move("f", 2, 1)
            elif command == "back":
                self.servo.move("b", 2, 1)
            elif command == "mid":
                self.servo.stop()
            elif command == "left":
                self.servo.move("l", 2, 1)
            elif command == "right":
                self.servo.move("r", 2, 1)
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
        self.camera.stop()


if __name__ == '__main__':
    agv = AGV(2)
    try:
        agv.subscribe()
        streaming_thread = threading.Thread(target=agv.send_frame, daemon=True)
        streaming_thread.start()
        while True:
            pass
    except KeyboardInterrupt:
        agv.terminate()

