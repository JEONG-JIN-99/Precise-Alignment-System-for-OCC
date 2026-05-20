# 한번 QR 인식 후 종료
import time

from qr.scanner import SmartPhoneScanner

class OneShotQRScanner(SmartPhoneScanner):
    def __init__(self, ip, port="8080"):
        super().__init__(ip, port)
        self.detected_result = None

    
    # QR 인식 시 실행하는 함수
    # input: 인식된 코드 타입, 인식된 데이터, 거리(카메라와 QR 중심 간의 픽셀 거리)
    # output: 없음 그냥 인식된 결과 self.detected_result 딕셔너리로 저장
    def on_detect(self, b_type, data, distance):
        self.detected_result = {
            "type": b_type,
            "data": data,
            "distance_px": distance,
        }

    # 한번 QR 인식 후 종료
    # input: 인식 시간 제한(초)
    # output: 인식된 결과 elf.detected_result 딕셔너리 반환
    def scan_once(self, timeout_sec=3.0):
        # 카메라 연결 확인
        if not self.cap or not self.cap.isOpened():
            if not self.connect():
                return None
        # 인식된 결과 초기화
        self.detected_result = None
        start_time = time.time()

        # 인식 시간 제한 동안 프레임 읽음음
        while time.time() - start_time < timeout_sec:
            success, frame = self.cap.read()
            if not success:
                continue

            # 프레임에서 qr 찾기
            # process_frame 함수에서 on_detect 함수 실행
            self.process_frame(frame)

            if self.detected_result is not None:
                return self.detected_result

        return None