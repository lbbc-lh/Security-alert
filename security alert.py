import RPi.GPIO as GPIO
import time
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from pubnub.exceptions import PubNubException

# 设置GPIO模式
GPIO.setmode(GPIO.BCM)

# 定义引脚
TRIG_PIN = 23
ECHO_PIN = 24
BUZZER_PIN = 4

# 设置引脚模式
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# PubNub配置
pnconfig = PNConfiguration()
pnconfig.publish_key = 'your_publish_key'
pnconfig.subscribe_key = 'your_subscribe_key'
pnconfig.ssl = True

pubnub = PubNub(pnconfig)

def measure_distance():
    # 触发超声波脉冲
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    # 初始化起始时间和结束时间
    start_time = time.time()
    stop_time = time.time()

    # 保存发出脉冲的开始时间
    while GPIO.input(ECHO_PIN) == 0:
        start_time = time.time()

    # 保存接收到回波信号的返回时间
    while GPIO.input(ECHO_PIN) == 1:
        stop_time = time.time()

    # 计算时间差
    time_elapsed = stop_time - start_time
    # 计算距离（声速34300 cm/s）
    distance = (time_elapsed * 34300) / 2

    return distance

def send_data_to_pubnub(distance, new_delay):
    try:
        envelope = pubnub.publish().channel('sensor_data').message({
            'distance': distance,
            'buzzer_duration': new_delay
        }).sync()
        print("publish timetoken: %d" % envelope.result.timetoken)
    except PubNubException as e:
        print(e)

try:
    while True:
        distance = measure_distance()
        new_delay = (distance * 3) + 30
        print(f"Measured Distance = {distance:.1f} cm")

        send_data_to_pubnub(distance, new_delay)

        if distance < 50:
            GPIO.output(BUZZER_PIN, GPIO.HIGH)
            time.sleep(new_delay / 1000)  # 将延迟从毫秒转换为秒
            GPIO.output(BUZZER_PIN, GPIO.LOW)
        else:
            GPIO.output(BUZZER_PIN, GPIO.LOW)

        time.sleep(0.2)  # 延迟200毫秒

except KeyboardInterrupt:
    print("Measurement stopped by User")
    GPIO.cleanup()
