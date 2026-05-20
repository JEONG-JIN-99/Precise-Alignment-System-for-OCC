# OCC 통신을 위한 정렬 시스템 (Alignment System for OCC)
# jj 브랜치가 현재 최신 버전 반드시 jj 브랜치를 볼 것 
Optical Camera Communication(OCC) 통신을 위한 GPS UWB 기반의 짐벌 정렬 및 제어 시스템입니다. 클라이언트-서버 구조를 통해 센서 데이터를 주고받으며, QR 코드 인식 및 데이터 로깅 기능을 포함하고 있습니다.

---

## 📂 프로젝트 구조 및 주요 기능 (Directory Structure)

### 🛰️ Connection & Core (클라이언트 / 서버)
* **`server/socket_server_test.py`**
  * 백그라운드에서 상시로 정보를 수신합니다. (GPS만 UWB는 구현 X)
  * 10개의 값을 읽어와서 초기 헤딩으로 설정 정렬 명령을 10번 반복하며 실험 데이터를 기록합니다.
  * 실험이 끝나면 짐벌을 0도로 초기화합니다.
* **`server/socket_server.py`**
  * 백그라운드에서 상시로 정보를 수신합니다. (GPS만 UWB는 구현 X)
  * 정렬 명령 하달 시, 수신된 정보를 기반으로 짐벌을 정렬하고 실험 데이터를 기록합니다.
  * 작동 30초 후에 짐벌을 0도로 초기화합니다.
* **`client/socket_client.py`**
  * GPS 모듈로부터 Raw 데이터를 받아 서버로 실시간 전송합니다.(GPS만 UWB는 구현 X)

### 🎮 Control (짐벌 제어)
* **`gimbal/gimbal_controller_yaw.py`**
  * 수신된 GPS 위치 데이터를 기반으로 짐벌의 Yaw 각도 및 서보 모터 제어를 위한 Duty Cycle을 계산합니다.
  * *(현재 UWB 기반 제어는 구현되어 있지 않습니다.)*

### 📷 Vision (QR 코드 프로세싱)
* **`qr/scanner.py`**
  * 카메라를 통해 QR 코드를 인식하고 스캔하는 소스코드입니다.
* **`qr/dist.py`**
  * 인식된 QR 코드의 중앙점과 카메라 화면 중심부 사이의 이격 거리를 계산합니다.

### 🔌 Sensors (센서 데이터 파싱)
* **`gps/sensor.py`**
  * GPS 모듈에서 들어오는 Raw 데이터를 파싱하여 유효한 위치 정보로 변환합니다.
* **`uwb/sensor.py`**
  * UWB(Ultra-Wideband) Raw 데이터를 파싱하는 코드입니다. *(현재 미구현)*

### 📊 Logging (데이터 기록)
* **`logger/result_logger.py`**
  * 실험 중 발생하는 주요 데이터 및 원하는 측정값을 프로젝트 루트 디렉토리 하위의 `result/` 폴더 내에 CSV 파일로 기록합니다.

---

## ⚠️ 참고 사항 (Status Notes)
* **미구현 기능:** `client/socket_client.py`, `uwb/sensor.py` 및 `gimbal/gimbal_controller_yaw.py` 내의 UWB 관련 로직은 현재 구현되지 않은 상태입니다.
