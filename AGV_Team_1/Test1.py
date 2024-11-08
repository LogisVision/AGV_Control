from RecogWorkingArea import *
from RoadFollowing import *
from jetbot import Robot
import time

if __name__ == '__main__':
    idx = 0
    color = ['yellow', 'orange', 'green', 'purple', 'blue', 'red']
    robot = Robot()  # Robot 객체는 한 번만 생성

    try:
        while idx < len(color):
            stop_event = threading.Event()
            
            # 매 반복마다 새로운 스레드 객체 생성
            recog_working_area = RecogWorkingArea(2, stop_event)
            road_following = RoadFollowing(2, stop_event)
            
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

            # 로봇 동작
            print("Moving forward...")
            robot.forward(0.5)
            time.sleep(3)
            robot.stop()
            time.sleep(2)
            
            idx += 1

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
        robot.stop()