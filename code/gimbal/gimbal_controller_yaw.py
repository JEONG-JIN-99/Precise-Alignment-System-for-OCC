import math
import time
import RPi.GPIO as GPIO

# packet set
# header | distance | azimuth | elevation | latitude | langitude
#                      방위각     고도각        위도        경도

class GimbalController:
    def __init__(self, yaw_pin=18):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(yaw_pin, GPIO.OUT)
        
        self.yaw_pwm = GPIO.PWM(yaw_pin, 50)
        self.yaw_pwm.start(7.5)   # 90도 대기

        #현재 짐벌의 물리적 각도를 저장 (초기값 90도)
        self.current_degree = 90.0
        # 서보 모터의 사양에 따른 동작 속도 (초당 회전 가능한 각도)
        # SG995 서보 기준: 0.2초당 60도 이동 가능(4.8V 기준)
        self.SERVO_SPEED_SEC_PER_DEG = 0.2 / 60.0

        print("Gimbal Initialized")
        time.sleep(1.0)

    # non-heading
    # input: 내 위치(my_pos)와 타겟 위치(target_pos)의 위도, 경도 값
    # output: 라디안 값으로 방위각 반환 
    def calculate_gps_angles(self, my_pos, target_pos):
        """
        GPS 기반 방위각(Yaw) 계산
        pos 형식: (lat, lon)
        """
        my_lat, my_lon = map(math.radians, my_pos)
        # print(my_lat, my_lon)
        tar_lat, tar_lon = map(math.radians, target_pos)
        # print(tar_lat, tar_lon)

        # 1. Yaw (Bearing) 계산
        d_lon = tar_lon - my_lon

        y = math.sin(d_lon) * math.cos(tar_lat)
        x = math.cos(my_lat) * math.sin(tar_lat) - \
            math.sin(my_lat) * math.cos(tar_lat) * math.cos(d_lon)
        
        yaw = math.atan2(y, x)
        return yaw

    # 북쪽을 바라보고 있다는 제약 (아래의 코드 사용하려면, 기존 gimbal의 각도(current_heading)에 대해 알고 있어야함.)
    def get_rotation_angle(self, my_pos, target_pos, current_heading):
        """
        current_heading: 센서(나침반 등)로 측정한 현재 내 장비의 정면 방향 (0~360도)
        """
        # 1. 타겟의 절대 방위각 계산 (기존 코드 활용)
        target_bearing_rad = self.calculate_gps_angles(my_pos, target_pos)
        print("target_bearing_rad", target_bearing_rad)
        current_heading_rad = math.radians(current_heading)
        print("current_heading_rad", current_heading_rad)

        # 3. 상대 각도 계산 (목표 - 현재)
        relative_rad = target_bearing_rad - current_heading_rad
        print("relative_rad", relative_rad)

        # 4. -pi ~ pi 범위로 정규화 (가장 가까운 회전 방향 선택)
        while relative_rad > math.pi: relative_rad -= 2 * math.pi
        while relative_rad < -math.pi: relative_rad += 2 * math.pi
        print("relative_rad after while", relative_rad)

        return relative_rad

        # # 2. 실제 회전해야 할 상대 각도 계산
        # # (타겟 방향 - 내 현재 방향)
        # relative_angle = target_bearing - current_heading

        # # 3. 결과값을 -180 ~ 180 사이로 정규화 (가까운 쪽으로 돌기 위해)
        # if relative_angle > 180:
        #     relative_angle -= 360
        # elif relative_angle < -180:
        #     relative_angle += 360

        # return relative_angle  # 이 값만큼 모터를 돌려야 함


    def calculate_uwb_angles(self, my_pos, target_pos):
        """
        target_pos: [distance, azimuth, elevation]
        이미 상대 각도로 들어오는 경우
        """
        # target_pos[1]이 Azimuth(방위각)이므로 이를 바로 사용
        yaw = target_pos[1]
        
        # 만약 방위각 범위가 -180~180이라면 0~360으로 변환 (필요시)
        # yaw = (yaw_ + 360) % 360
        
        return yaw

    # input: 라디안 값으로 들어오는 방위각
    # output: 서보 모터 이동
    def move_to(self, relative_rad):
        """
        상대 라디안 값을 받아 서보 모터 이동
        relative_rad: -pi/2 (-90도) ~ pi/2 (90도) 범위를 주동력으로 사용
        """
        # 1. 라디안을 각도(Degree)로 변환
        # 디버깅 표시용 각도는 -90~90도 기준으로 사용
        input_az_degree = math.degrees(relative_rad)

        # 상대 각도 0(정면)일 때 서보 90도 위치로 맵핑
        # target_degree: 0~180도 범위를 주동력으로 사용 모터는 반시계 방향으로 회전을 함
        target_degree = input_az_degree + 90
        
        # 2. 물리적 한계 제한 (0~180도)
        # 서보는 180도 이상 돌 수 없으므로 클램핑(Clamping)
        if target_degree < 0:
            target_degree = 0
        elif target_degree > 180:
            target_degree = 180

        # 내부 0~180도 값을 다시 디버깅용 -90~90도 값으로 변환
        target_az_degree = target_degree - 90
        current_az_degree = self.current_degree - 90

        # # [핵심 수정] 기어 반전 적용
        # # 실제 기계가 target_degree(예: 120도)로 가길 원한다면, 
        # # 반대로 도는 모터는 (180 - 120) = 60도 지점으로 명령을 내려야 합니다.
        # motor_target_degree = 180.0 - target_degree

        # 3. 현재 각도와 목표 각도의 차이(이동 거리) 계산
        delta_degree = abs(target_degree - self.current_degree)

        # 4. PWM 적용
        # 반대반향 회전 기어를 고려한 듀티 사이클 계산
        duty = (target_degree / 18.0) + 2.5
        self.yaw_pwm.ChangeDutyCycle(duty)

        # 5. 이동할 각도에 비례하여 물리적으로 회전할 때까지 CPU를 붙잡아둠 (Blocking)
        move_time = delta_degree * self.SERVO_SPEED_SEC_PER_DEG
        
        # 급격한 반전 시 모터의 부하(관성)를 고려해 최소 대기 시간이나 마진(예: +0.05초)을 더해주면 더 안정적
        if move_time > 0:
            time.sleep(move_time + 0.05) # 20ms 마진 추가

        # 이동이 끝났으므로 듀티 사이클을 0으로 만들어 신호를 차단합니다.
        # 이렇게 하면 모터 내부 모스펫이 열을 받거나 지터링이 생기는 것을 완전히 방지합니다.
        self.yaw_pwm.ChangeDutyCycle(0)

        # 6. 이동이 끝났으므로 현재 위치를 목표 위치로 갱신
        self.current_degree = target_degree
        print(
            "\n[ GIMBAL MOVE ]\n"
            f"입력 각도      : {input_az_degree:.2f}도\n"
            f"현재 각도      : {current_az_degree:.2f}도\n"
            f"이동 후 각도   : {target_az_degree:.2f}도\n"
            f"모터 명령      : {target_degree:.2f}도\n"
            f"Duty Cycle     : {duty:.4f}\n"
            f"이동량         : {delta_degree:.2f}도\n"
            f"이동 시간      : {move_time:.4f}s\n"
            "[ /GIMBAL MOVE ]"
        )
        
        return delta_degree

    def cleanup(self):
        self.yaw_pwm.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    gimbal = GimbalController()
    # my_pos = [35.134739, 129.102724]
    # # target_pos = [35.134505, 129.102517] # bench
    # target_pos = [35.135144, 129.102290] # park
    # current_heading = 0.0 # 북쪽 방향 기준
    # yaw = gimbal.calculate_gps_angles(my_pos, target_pos)
    # print(yaw)
    gimbal.move_to(math.radians(-90))
    time.sleep(5)
    gimbal.move_to(math.radians(90))
    time.sleep(5)
