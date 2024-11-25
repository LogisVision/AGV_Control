from RecogWorkingArea import *
from RoadFollowing import *
from ArmServo import *
from jetbot import Robot
import time, sys

if __name__ == '__main__':
    idx = 0
    color = ['yellow', 'green']
    # color = ['green']
    servo = AGVTeamTwoServo()

    try:
        while (idx < len(color)):
            stop_event = threading.Event()
            stop_event.clear()
            
            # 매 반복마다 새로운 스레드 객체 생성
            recog_working_area = RecogWorkingArea("B", stop_event)
            road_following = RoadFollowing("B", stop_event)
            
            # 현재 찾을 색상 설정
            recog_working_area.working_areas = [color[idx]]
            print(f"Looking for color: {color[idx]}")

            # 스레드 시작
            recog_working_area.start()
            road_following.start()

            # 이벤트 대기
            while not stop_event.is_set():
                time.sleep(0.1)  # CPU 부하 감소

            print(f"Detected {color[idx]}!")
            
            # 스레드 정리
            recog_working_area.stop()
            road_following.stop()
            recog_working_area.join()
            road_following.join()

            time.sleep(2)

            # 로봇 동작
            # print("Moving forward...")
            # stop_event.clear()
            # road_following = RoadFollowing(2, stop_event)
            # road_following.start()
            # time.sleep(3)
            # road_following.stop()
            # road_following.join()
            
            # servo.reset_degree()
            # time.sleep(2)
            # servo.operate_arm(1, -90)
            # time.sleep(1)

            # servo.operate_arm(3, servo.grap_box_degree[3])
            # time.sleep(8)
            # servo.operate_arm(2, servo.grap_box_degree[2])
            # time.sleep(8)
            # servo.operate_arm(4, servo.grap_degree)
            # time.sleep(1)

            idx += 1
        sys.exit(0)

    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    finally:
        # 프로그램 종료 시 정리
        if 'recog_working_area' in locals():
            recog_working_area.stop()
            recog_working_area.join()
        if 'road_following' in locals():
            road_following.stop()
            road_following.join()
        servo.stop()