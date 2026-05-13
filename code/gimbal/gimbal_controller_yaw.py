import math
import RPi.GPIO as GPIO
import time

# packet set
# header | distance | azimuth | elevation | latitude | langitude
#                      방위각     고도각        위도        경도

class GimbalController:
    def __init__(self, yaw_pin=18):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(yaw_pin, GPIO.OUT)
        
        self.yaw_pwm = GPIO.PWM(yaw_pin, 50)
        
        self.yaw_pwm.start(7.5)
        # time.sleep(0.1)
        self.move_to(0.0)
        # time.sleep(0.1)
        
        print("Gimbal Initialized")

    # non-heading
    #Output : -pi ~ pi (정북 기준 각도)
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
        # print("target_bearing_rad", target_bearing_rad)
        current_heading_rad = math.radians(current_heading)
        # print("current_heading_rad", current_heading_rad)

        # 3. 상대 각도 계산 (목표 - 현재)
        relative_rad = target_bearing_rad - current_heading_rad
        # print("relative_rad", relative_rad)

        # 4. -pi ~ pi 범위로 정규화 (가장 가까운 회전 방향 선택)
        while relative_rad > math.pi: relative_rad -= 2 * math.pi
        while relative_rad < -math.pi: relative_rad += 2 * math.pi
        # print("relative_rad after while", relative_rad)

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


    # def move_to(self, relative_rad):
    #     """
    #     상대 라디안 값을 받아 서보 모터 이동
    #     relative_rad: -pi/2 (-90도) ~ pi/2 (90도) 범위를 주동력으로 사용
    #     """
    #     # 1. 라디안을 각도(Degree)로 변환
    #     # 상대 각도 0(정면)일 때 서보 90도 위치로 맵핑
    #     target_degree = math.degrees(relative_rad) + 90
    #     print(target_degree)
    #     # 2. 물리적 한계 제한 (0~180도)
    #     # 서보는 180도 이상 돌 수 없으므로 클램핑(Clamping)
    #     if target_degree < -90:
    #         target_degree = -90
    #     elif target_degree > 90:
    #         target_degree = 90

    #     # 3. PWM 적용
    #     print("target_degree", target_degree)
    #     duty = (target_degree / 18.0) + 2.5
    #     print("duty", duty)
    #     self.yaw_pwm.ChangeDutyCycle(duty)
    #     # print(f"Target Rad: {relative_rad:.4f}, Servo Deg: {target_degree:.2f}")

    # Input : -pi ~ pi (정북 기준 각도)
    # Output : 2.5 ~ 12.5 (Duty Cycle)
    def move_to(self, relative_rad):
        """
        relative_rad: -pi ~ pi (상대 라디안)
        - 0 rad: 정면 (Duty 7.5)
        - -pi/2 rad (-90도): 왼쪽 끝 (Duty 2.5)
        - pi/2 rad (90도): 오른쪽 끝 (Duty 12.5)
        """
        # 1. 라디안 범위 제한 (-pi/2 ~ pi/2)
        # 서보의 물리적 한계가 180도이므로 그 이상의 라디안은 잘라냅니다.
        half_pi = math.pi / 2
        if relative_rad < -half_pi:
            relative_rad = -half_pi
        elif relative_rad > half_pi:
            relative_rad = half_pi

        # 2. 라디안을 바로 Duty Cycle로 변환하는 공식
        # (relative_rad / pi) * 10 + 7.5
        """
        설명: 
        -pi/2 대입 시: (-0.5 * 10) + 7.5 = 2.5
        0 대입 시: (0 * 10) + 7.5 = 7.5
        pi/2 대입 시: (0.5 * 10) + 7.5 = 12.5
        """

        # 양수(+)일 때 오른쪽으로 회전 # 기어로 인해서 거꾸로 작동해야 최종적인 방향이 맞아짐
        duty = (relative_rad / math.pi) * 10.0 + 7.5

        # 양수(+)일 때 왼쪽으로 회전 (방향 반전) 
        # duty = 7.5 - (relative_rad / math.pi) * 10.0
        
        # 만약 결과가 2.5 미만이나 12.5를 넘으면 클램핑
        duty = max(2.5, min(12.5, duty))
        
        # 3. PWM 적용
        print(f"Input Rad: {relative_rad:.4f}, Calculated Duty: {duty:.2f}")
        self.yaw_pwm.ChangeDutyCycle(duty)


    def cleanup(self):
        self.yaw_pwm.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    try:
        gimbal = GimbalController()
        my_pos = [35.134739, 129.102724]
        # target_pos = [35.134505, 129.102517] # bench
        # target_pos = [35.135144, 129.102290] # park
        # target_pos = [35.135024, 129.103050] # N,E
        target_pos = {
            "bench" : [35.134505, 129.102517],
            "park" : [35.135144, 129.102290],
            "ne" : [35.135024, 129.103050]
        }
        place_name = "park"
        current_heading_rad = math.radians(0.0) # 북쪽 방향 기준
        yaw = gimbal.get_rotation_angle(my_pos, target_pos.get(place_name), current_heading_rad)
        print("place_name : ", place_name)
        print(yaw)
        # gimbal.move_to(0.0) # Duty 7.5 90도로 head setting
        # gimbal.move_to(yaw)
        # time.sleep(1)
        # gimbal.move_to(1)
        # time.sleep(1)

    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        gimbal.cleanup()
        print("GPIO Cleaned up")