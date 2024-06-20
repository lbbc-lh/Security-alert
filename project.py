# import necessary libraries
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub, SubscribeListener
from pubnub.exceptions import PubNubException   # for sending data to frontend via pubnub platform
from picamera2 import Picamera2
import numpy as np
import io
import base64   # for capturing pictures and transferring to structured data
import time   # for recording the time info
import RPi.GPIO as GPIO   # for controling the ultrasonic sensor and actuator (buzzer)

# set the pubnub config
config = PNConfiguration()
config.publish_key = "pub-c-9d79be43-60ba-4e51-a889-8a85b4c29509"
config.subscribe_key = "sub-c-31f4e71c-c7ba-46c5-b2a7-661511e01554"
config.uuid = "769channel"
pubnub = PubNub(config)

# initialize the camera
camera = Picamera2()
config = camera.create_still_configuration(main = {"size": (128, 128)})   # set the picture size
camera.configure(config)


# set the GPIO mode, define the pins, and setup pins
GPIO.setmode(GPIO.BCM)
TRIG_PIN = 23
ECHO_PIN = 24
BUZZER_PIN = 4
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# define functions to measure distance and capture pictures
def measure_distance():
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)
    start_time = time.time()
    stop_time = time.time()
    while GPIO.input(ECHO_PIN) == 0:
        start_time = time.time()
    while GPIO.input(ECHO_PIN) == 1:
        stop_time = time.time()
    time_elapsed = stop_time - start_time
    distance = (time_elapsed * 34300) / 2   # calculate the distance with the sound speed
    return distance

def capture_picture():
    camera.start()
    buffered = io.BytesIO()
    # capture
    camera.capture_file(buffered, format='jpeg')
    camera.stop()
    # encode using base64 and decode to string
    pic_data = base64.b64encode(buffered.getvalue()).decode()
    print(pic_data)
    buffered.close()
    return pic_data

try:
    while True:
        # measure the distance every 2 seconds
        distance = measure_distance()
        print(f"Measured Distance = {distance:.4f} cm")
        # detect any possible items within 10cm
        if distance < 10:
            time_data = time.time()   # record the time
            pic_data = capture_picture()   # capture the picture
            
            # send the data
            message = {
                "timestamp": time_data,
                "dis_data": distance,
                "pic_data": pic_data
            }
            envelope = pubnub.publish().channel("769channel").message(message).use_post(True).sync()
            
            # activate the buzzer for 1 second as warning
            GPIO.output(BUZZER_PIN, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(2)
except KeyboardInterrupt:
    print("Measurement stopped by User")
    GPIO.cleanup()


'''
# camera sensor capture
camera = Picamera2()
config = camera.create_still_configuration(main = {"size": (128, 128)})
camera.configure(config)
#camera.start_and_capture_file("1.jpeg")
camera.start()
image = camera.capture_array()
camera.stop()

buffered = io.BytesIO()
buffered.write(image.tobytes())
# get the bytes in the buffer, base64 encode, then decode to string
pic_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
print(pic_data)
chunk_size = 7200
chunks = [pic_data[i: i+chunk_size] for i in range(0, len(pic_data), chunk_size)]
for i, chunk in enumerate(chunks):
    message = {"img_chunk": chunk, "img_index": i, }
    envelope = pubnub.publish().channel("769channel").message(message).use_post(True).sync()
print(len(chunks))
'''