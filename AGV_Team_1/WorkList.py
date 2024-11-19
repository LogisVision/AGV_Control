from RecogWorkingArea import *
from RoadFollowing import *
from jetbot import Robot
import time
import paho.mqtt.client as mqtt
from queue import Queue
import threading

class WorkType:
    PICKUP = "pickup"
    DROPOFF = "dropoff"
    
    @classmethod
    def is_valid(cls, command: str) -> bool:
        command_type = command.split(',')[0]
        return command_type in [cls.PICKUP, cls.DROPOFF]


def on_connect(client, userdata, flags, rc):
    print("연결됨: "+str(rc))
    client.subscribe("jetbot/command")

def on_message(client, userdata, msg):
    try:
        command = msg.payload.decode().strip().lower()
        if WorkType.is_valid(command):
            # 명령어를 타입과 위치로 분리
            parts = command.split()
            work_type = parts[0]
            workspace = parts[1] if len(parts) > 1 else None
            
            work_info = {
                'type': work_type,
                'workspace': workspace
            }
            
            work_queue.put(work_info)
            print(f"작업 추가됨: {work_type} at {workspace}")
        else:
            print(f"잘못된 작업 타입: {command}")
    except Exception as e:
        print(f"메시지 처리 중 오류 발생: {e}")
    
def process_work():
    while True:
        try:
            # Queue에서 작업 가져오기 (작업이 없으면 대기)
            work_info = work_queue.get()
            work_type = work_info['type']
            workspace = work_info['workspace']
            print(f"새로운 작업 시작: {work_type} at {workspace}")
            
            start_threads(work_info)
            
            # 작업 완료 표시
            work_queue.task_done()
            
        except Exception as e:
            print(f"작업 처리 중 오류 발생: {e}")
            continue

def start_threads(work_info):
    global recog_working_area, road_following
    # work_type = work_info['type']
    # workspace = work_info['workspace']

    
    stop_event = threading.Event()
    current_color = work_info['workspace']
    current_work_type = work_info['type']
    
    # 새로운 쓰레드 객체 생성
    recog_working_area = RecogWorkingArea(2, stop_event)
    road_following = RoadFollowing(2, stop_event)
    
    # 현재 찾을 색상 설정
    recog_working_area.working_areas = [current_color]
    print(f"찾고있는 색상: {current_color}")

    # 쓰레드 시작
    recog_working_area.start()
    road_following.start()

    # 이벤트 대기
    while not stop_event.is_set():
        time.sleep(0.1)

    print(f"{current_color} 감지됨!")
    
    # 쓰레드 정리
    cleanup_threads()
    
    # 로봇 동작
    print("전진 중...")
    robot.forward(0.5)
    time.sleep(3)
    robot.stop()
    
    # 작업 타입에 따라서 다른 동작 수행
    if current_work_type == 'pickup':
        # TODO 픽업 동작 추가
        print("픽업 중...")
    elif current_work_type == 'dropoff':
        # TODO 놓기 동작 추기
        print("물건을 자리에 놓는 중...")

def cleanup_threads():
    if 'recog_working_area' in globals():
        recog_working_area.stop()
        recog_working_area.join()
    if 'road_following' in globals():
        road_following.stop()
        road_following.join()

if __name__ == '__main__':
    color = ['yellow', 'orange', 'green', 'purple', 'blue', 'red']
    robot = Robot()
    
    # 작업 큐 생성
    work_queue = Queue()

    # MQTT 클라이언트 설정
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # 작업 처리 쓰레드 시작
    work_processor = threading.Thread(target=process_work, daemon=True)
    work_processor.start()

    try:
        # MQTT 브로커 연결
        client.connect("브로커주소", 1883, 60)
        client.loop_start()

        # 메인 루프
        while True:
            if work_queue.empty():
                print("대기 중... 새로운 작업을 기다리는 중")
            time.sleep(5)  # 5초마다 상태 출력

    except KeyboardInterrupt:
        print("\n사용자에 의해 프로그램이 종료되었습니다")
    finally:
        cleanup_threads()
        robot.stop()
        client.loop_stop()
        client.disconnect()