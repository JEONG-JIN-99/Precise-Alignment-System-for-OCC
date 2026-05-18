import socket
from gimbal.gimbal_controller_yaw import GimbalController
import time
import threading
from gps.sensor import GPS
from uwb.sensor import UWB

# --- 설정 ---
UDP_IP = "0.0.0.0"
UDP_PORT = 5005

# 짐벌 객체 생성
gimbal = GimbalController(yaw_pin=18)

# 소켓 설정
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# GPS 객체 생성
gps = GPS(port='/dev/ttyUSB0')
location = gps.get_location()

# 백그라운드에서 최신 데이터를 저장할 글로벌 변수와 충돌 방지 락(Lock)
latest_data_info = None
# data_lock: 데이터 충돌 방지를 위한 키
data_lock = threading.Lock()

def udp_receiver_thread():
    """
    백그라운드에서 계속 실행되며 최신 타겟 위치 데이터를 갱신하는 함수
    """
    global latest_data_info
    print(f"Background receiver started at {UDP_PORT}...")
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            recv_time_ns = time.time_ns()
            
            # Lock을 걸고 최신 데이터 갱신
            with data_lock:
                latest_data_info = (data, recv_time_ns)
        except Exception as e:
            print(f"[Thread Error] {e}")

# 스레드 실행 (데몬 스레드로 설정하여 메인 프로그램 종료 시 함께 종료되도록 함)
receiver_thread = threading.Thread(target=udp_receiver_thread, daemon=True)
receiver_thread.start()

print("\n=== 짐벌 제어 서버가 준비되었습니다 ===")
print("명령 대기 중... (엔터키를 누르면 최신 타겟 위치로 정렬합니다. 'q'를 누르면 종료)")

try:
    while True:
        # 사용자 명령 대기 (Blocking)
        command = input("\n명령을 입력하세요 [엔터: 정렬, q: 종료] : ")
        
        if command.lower() == 'q':
            break
            
        # 명령이 떨어졌을 때, 락을 걸고 가장 최신 데이터를 가져옴
        with data_lock:
            current_target = latest_data_info
            
        if current_target is None:
            print("아직 클라이언트로부터 수신된 데이터가 없습니다. 조금 더 기다려주세요.")
            continue
            
        # 데이터 분해
        data, gps_recv_time_ns = current_target
        
        # 명령을 내린 시점 (수동 명령이므로, 인간의 명령 시점을 기준으로 삼는 것이 좋습니다)
        command_time_ns = time.time_ns()

        try:
            msg_str = data.decode('utf-8')
            parts = msg_str.split(',')
            header = parts[0]

            if header == "1": # UWB 모드
                dist, az, el = map(float, parts[1:4])
                yaw = az 
                gimbal.move_to(yaw)
                print(f"[UWB] Target Az: {az} | Gimbal Yaw: {yaw:.2f}°")

            else: # GPS 모드
                my_pos = (37.5, 127.0) 
                target_pos = [float(parts[4]), float(parts[5])] 
                gps_read_time_ns = int(parts[6])

                yaw = gimbal.calculate_gps_angles(my_pos, target_pos)
                gimbal.move_to(yaw)

                # 참고: 데이터 송신부터 수신까지의 지연 시간 (이건 백그라운드 수신 기준이므로 그대로 써도 됨)
                tx_latency_ms = (gps_recv_time_ns - gps_read_time_ns) / 1_000_000.0
                print(f"tx_latency_ms: {tx_latency_ms:.2f} ms")
                print(f"[GPS Target] Data: {parts}")

            # [수정 포인트] 정렬 시간 계산
            align_recog_done_time_ns = time.time_ns()
            
            # 주의: 데이터 수신 시점(gps_recv_time_ns)을 기준으로 빼버리면, 사용자가 엔터를 누르기까지 
            # 고민한 시간(수 초~수 분)이 포함되어 버립니다. 
            # 따라서 '명령을 내린 시점(command_time_ns)'을 빼주는 것이 물리적 구동 시간을 재는 데 더 정확합니다.
            align_recog_time_ms = (align_recog_done_time_ns - command_time_ns) / 1_000_000.0
            print(f"정렬 및 인식 소요 시간 (Alignment Time): {align_recog_time_ms:.2f} ms")

        except Exception as e:
            print(f"Data processing error: {e}")

except KeyboardInterrupt:
    print("\n강제 종료됨...")
finally:
    print("\nShutting down server...")
    gimbal.cleanup()
    sock.close()