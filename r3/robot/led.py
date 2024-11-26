import RPi.GPIO as GPIO
from time import sleep

LED_PIN = 13

GPIO.setwarnings(False)

# BCM numbering
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

while True:
    GPIO.output(LED_PIN, GPIO.HIGH)
    sleep(1)
    GPIO.output(LED_PIN, GPIO.LOW)
    sleep(1)    