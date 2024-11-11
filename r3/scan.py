
from pad4pi import rpi_gpio
import time
import RPi.GPIO as GPIO
import sys
import serial

RFID_EN_PIN = 4

GPIO.setwarnings(False)

# BCM numbering
GPIO.setmode(GPIO.BCM)

GPIO.setup(RFID_EN_PIN, GPIO.OUT)
GPIO.output(RFID_EN_PIN, GPIO.HIGH)

#port = '/dev/ttyAMA0'
port = '/dev/ttyS0'
ser = serial.Serial(port,38400,8)
ser.port = port
ser.baudrate = 38400
time.sleep(0.2)

cmd_fw_version = b'\x0A\x56\x0D'
cmd_reader_id = b'\x0A\x53\x0D'
cmd_Q_EPC = b'\x0A\x51\x0D'
cmd_MQ_EPC = b'\x0A\x55\x0D'
#read power 00 - 1B 27 level -2 to 25 db
#0A 4E 30 2C 30 30 0D -- -2
#0A 4E 30 2C 31 42 0D -- -2
cmd_Reader_Power_Max = b'\x0A\x4E\x30\x2C\x31\x42\x0D'

KEYPAD = [
    [1, 2, 3, 4],
    [5, 6, 7, 8],
    [9, 10, 11, 12],
    [13,14, 15, 16]
]

'''
# Set the Column Pins
COL_1 = 17
COL_2 = 27
COL_3 = 22
COL_4 = 5

# Set the ROW Pins
ROW_1 = 23
ROW_2 = 24
ROW_3 = 25
ROW_4 = 16
'''

#ROW_PINS = [17, 27, 22, 5] # BCM numbering
#COL_PINS = [23, 24, 25, 16] # BCM numbering

COL_PINS = [5, 22, 27, 17] # BCM numbering
ROW_PINS = [23, 24, 25, 16] # BCM numbering

items = []

def sys_cmd(CMD):
    ser.write(CMD)
    time.sleep(0.1)     

def run_cmd(CMD):
    print("Send command : ",CMD)
    ser.write(CMD)
    time.sleep(0.1)     
    while ser.inWaiting() > 0:
        x = ser.readline().strip()
        if x not in items and len(x)>10:
            items.append(x)
            print("items ",len(items),' is ',x)

def run_cmd2(CMD):
    print("Send command : ",CMD)
    while True:
        ser.write(CMD)
        time.sleep(0.1)     
        while ser.inWaiting() > 0:
            x = ser.readline().strip()
            if x not in items and len(x)>10:
                items.append(x)
                print("items ",len(items),' is ',x)

def print_key(key):
    print(f"Received key from interrupt:: {key}")
    match key:
        case 13:
            run_cmd(cmd_fw_version)
        case 9:
            run_cmd(cmd_reader_id)
        case 5:
            run_cmd(cmd_Q_EPC)
        case 1:#อ่านเป็นชุด loop
            run_cmd2(cmd_MQ_EPC)
        case 6:#อ่านเป็นชุด
            run_cmd(cmd_MQ_EPC)  
        case 15:#reset items
            items = []
            print("Reset items")
        case 11:#List items
            print(len(items),' items = ',items)
        case 16:
            exit()
        case _:
            print("No Command")


try:
    #init cmd
    sys_cmd(cmd_Reader_Power_Max)

    factory = rpi_gpio.KeypadFactory()
    keypad = factory.create_keypad(keypad=KEYPAD,row_pins=ROW_PINS, col_pins=COL_PINS) # makes assumptions about keypad layout and GPIO pin numbers

    keypad.registerKeyPressHandler(print_key)

    ser.reset_input_buffer()
    print("Press buttons on your keypad. Ctrl+C to exit.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Goodbye")
finally:
    keypad.cleanup()