import math
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
        print("Gimbal Initialized")

    #  북쪽 헤딩 기반
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
    # def get_rotation_angle(self, my_pos, target_pos, current_heading):
    #     """
    #     current_heading: 센서(나침반 등)로 측정한 현재 내 장비의 정면 방향 (0~360도)
    #     """
    #     # 1. 타겟의 절대 방위각 계산 (기존 코드 활용)
    #     target_bearing = self.calculate_gps_angles(my_pos, target_pos)

    #     # 2. 실제 회전해야 할 상대 각도 계산
    #     # (타겟 방향 - 내 현재 방향)
    #     relative_angle = target_bearing - current_heading

    #     # 3. 결과값을 -180 ~ 180 사이로 정규화 (가까운 쪽으로 돌기 위해)
    #     if relative_angle > 180:
    #         relative_angle -= 360
    #     elif relative_angle < -180:
    #         relative_angle += 360

    #     return relative_angle  # 이 값만큼 모터를 돌려야 함


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


    def move_to(self, yaw):
        """
        서보 모터 이동 (물리적 오프셋 적용)
        기본적으로 북쪽(0도)을 바라볼 때 서보를 90도 위치에 정렬한다고 가정
        """
        # 정북향(0도) 기준 서보 위치 조정 예시
        # 실제 장착 방향에 따라 + 또는 - 오프셋 조정이 필요합니다.
        target_yaw = (yaw % 180) 
        
        # 안전 제한
        target_yaw = max(0, min(180, target_yaw))

        self.yaw_pwm.ChangeDutyCycle((target_yaw / 18.0) + 2.5)

    def cleanup(self):
        self.yaw_pwm.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    gimbal = GimbalController()
    my_pos = [35.134739, 129.102724]
    # target_pos = [35.134505, 129.102517] # bench
    target_pos = [35.135144, 129.102290] # park
    yaw = gimbal.calculate_gps_angles(my_pos, target_pos)
    # print(yaw)
    gimbal.move_to(yaw)