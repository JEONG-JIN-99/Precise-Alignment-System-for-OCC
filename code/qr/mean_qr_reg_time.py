import time
import sys
import os

# 상위 폴더(code/)를 sys.path에 추가하여 패키지 임포트 문제 해결
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from qr.one_shot_scanner import OneShotQRScanner

def main():
    # IP Webcam 설정 (main.py의 설정을 그대로 사용)
    PHONE_IP = "192.168.0.6"
    PHONE_PORT = "8080"
    
    print("=== QR Code Recognition Time Measurement (100 Repetitions) ===")
    print(f"[*] Connecting to Camera Stream: http://{PHONE_IP}:{PHONE_PORT}/video")
    
    # OneShotQRScanner 객체 생성
    scanner = OneShotQRScanner(PHONE_IP, PHONE_PORT)
    
    # 카메라 스트림 연결 시도
    if not scanner.connect():
        print("[!] Error: Could not connect to camera stream. Please check IP/Port and network connection.")
        return

    print("\n[!] Connection Successful. Starting measurement in 2 seconds...")
    print("[!] Ensure the camera is aligned and directly facing the QR code.")
    time.sleep(2.0)  # 카메라 스트림이 안정화될 때까지 대기

    durations_ms = []
    success_count = 0
    
    for i in range(100):
        # 이전 결과 초기화
        scanner.detected_result = None
        
        # 정밀 시간 측정을 위해 perf_counter 사용
        start_time = time.perf_counter()
        
        # 1회 스캔 실행 (최대 5.0초 동안 인식 대기)
        result = scanner.scan_once(timeout_sec=5.0)
        
        end_time = time.perf_counter()
        
        if result is not None:
            duration = (end_time - start_time) * 1000.0
            durations_ms.append(duration)
            success_count += 1
            print(f"[Trial {i+1:03d}/100] Success: {duration:6.2f} ms | Data: {result['data']}")
        else:
            print(f"[Trial {i+1:03d}/100] Failed: Recognition Timeout (5.0s)")
            
        # 연속된 프레임 처리 간에 미세 버퍼 클리어 시간을 줌
        time.sleep(0.05)

    # 카메라 자원 해제
    scanner.stop()

    print("\n=================== RESULT SUMMARY ===================")
    if success_count > 0:
        avg_time = sum(durations_ms) / success_count
        min_time = min(durations_ms)
        max_time = max(durations_ms)
        print(f" Total Trials       : 100")
        print(f" Successful Trials  : {success_count}")
        print(f" Failed Trials      : {100 - success_count}")
        print(f" Average Recog Time : {avg_time:.2f} ms")
        print(f" Min Recog Time     : {min_time:.2f} ms")
        print(f" Max Recog Time     : {max_time:.2f} ms")
    else:
        print(" [!] No QR codes were recognized. Please ensure the QR code is clearly visible to the camera.")
    print("======================================================")

if __name__ == '__main__':
    main()
