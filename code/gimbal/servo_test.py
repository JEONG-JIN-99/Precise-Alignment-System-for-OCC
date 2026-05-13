import RPi.GPIO as GPIO
import time
"""
    H/W - MG995 Metal Gear Servo Motor
    A : 회전 축 포함 높이(z)
    B : 모터 몸체 길이(y)
    C : 회전 축 제외 높이(z)
    D : 모터 몸체 너비(x)
    E : 고정핀 포함 길이(y)
    F : 모터 고정핀 제외 높이(z)
"""
SERVO_PIN1 = 18
# SERVO_PIN2 = 12
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN1, GPIO.OUT)
# GPIO.setup(SERVO_PIN2, GPIO.OUT)

pwm1 = GPIO.PWM(SERVO_PIN1, 50) # MG995는 보통 50Hz
# pwm2 = GPIO.PWM(SERVO_PIN2, 50) # MG995는 보통 50Hz
pwm1.start(0)
# pwm2.start(0)

try:
    while True:
        # 서보 제어 로직
        # pwm1.ChangeDutyCycle(2.5) # 0도
        pwm1.ChangeDutyCycle(7.5) # 90도
        # pwm2.ChangeDutyCycle(7.5) # 90도
        time.sleep(1)
        # pwm1.ChangeDutyCycle(1) # ?도
        pwm1.ChangeDutyCycle(2.5) # 0도
        # pwm2.ChangeDutyCycle(2.5) # 0도
        time.sleep(1)
except KeyboardInterrupt:
    print("프로그램 종료")
    pwm1.ChangeDutyCycle(2.5)
    # pwm2.ChangeDutyCycle(2.5)
    time.sleep(0.5)
finally:
    pwm1.stop()        # PWM 정지
    # pwm2.stop()        # PWM 정지
    GPIO.cleanup()    # GPIO 설정 초기화