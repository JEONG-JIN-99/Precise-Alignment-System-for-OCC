import socket
from gimbal.gimbal_controller_yaw import GimbalController
import time
from gps.sensor import GPS
from uwb.sensor import UWB

"""
    평가 기준 후보 list :
    1. (server, client location signal + gimbal control) time
    -> 신호 처리 속도는 신호를 받는 거리(위성 vs transceiver)차이 때문에 아무래도 uwb가 빠를 것 같고,
    gimbal control도 각도 계산(gps는 후처리 필요, uwb는 PDoA로 바로 받음)차이 때문에 uwb가 빠를 것 같음. (당연한 이야기..?)
    
    2. (camera) position accuracy
    -> 카메라 중앙에서 얼마나 멀리 떨어져 있는지를 비교하는 방식, 시간과 같이 사용해야할 것 같긴함. 시간은 너무 뻔한 것 같아서.

    3. detecting time
    -> 내재적으로 QR을 감지하는 시간이 signal, gimbal control을 합친 시간이라, 근본적인 평가 기준은 아닌 듯 함.
"""

# --- 설정 ---
UDP_IP = "0.0.0.0"
UDP_PORT = 5005

# 짐벌 객체 생성
gimbal = GimbalController(yaw_pin=18)

# 소켓 설정
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
gps = GPS(port='/dev/ttyUSB0')
# time.slee(5) # 필요 시 활성화
location = gps.get_location()

print(f"Server started at {UDP_PORT}. Waiting for data...")

# if location: # UWB location 추가 필요. // server의 위치가 잡혀있는지 확인하는 과정.
try:
    while True:
        # 0. server(여기서는 gimbal)의 이동성에 따라, gps 신호의 update 필요성 있음.
        # gps.update()
        # 1. 데이터 수신
        data, addr = sock.recvfrom(1024)
        
        try:
            # 헤더 확인 (바이트 형태라면 data[0] 직접 접근)
            # 여기서는 송신측에서 "1,dist,az,el" 식의 문자열을 보낸다고 가정합니다.
            msg_str = data.decode('utf-8')
            parts = msg_str.split(',') # 쉼표로 구분된 데이터 분리
            header = parts[0]

            # 수신 데이터가 [dist, az, el] 형태라면
            if header == "1": # UWB 모드
                
                dist, az, el = map(float, parts[1:4])
                
                # 1. 만약 수신된 az가 이미 상대 각도라면 계산 함수 없이 바로 이동
                yaw = az 
                
                # 2. 만약 내 위치와 타겟의 '절대' 위치를 비교해야 한다면
                # (이 경우 target_pos가 [x, y, z] 좌표여야 함)
                # yaw = gimbal.calculate_uwb_angles(my_pos, [target_x, target_y, target_z])

                gimbal.move_to(yaw)
                # print(f"[UWB] Target Az: {az} | Gimbal Yaw: {yaw:.2f}°")


            else: # GPS 모드 (header가 "1"이 아닌 경우)
                # 내 RTK GPS 위치 (Lat, Lon)
                # my_pos = gps.get_location()
                my_pos = (37.5, 127.0) 
                
                # 수신 데이터: [latitude, longitude]
                # 패킷 구조에 따라 인덱스를 조정하세요. (예: parts[4:6])
                target_pos = list(map(float, parts[4:])) 
                
                yaw = gimbal.calculate_gps_angles(my_pos, target_pos)
                gimbal.move_to(yaw)
                # print(f"[GPS target] Lat: {target_pos[0]}, Lon: {target_pos[1]} | Yaw: {yaw:.2f}°")

        except Exception as e:
            print(f"Data processing error: {e}")

except KeyboardInterrupt:
    print("\nShutting down server...")
finally:
    gimbal.cleanup()
    sock.close()