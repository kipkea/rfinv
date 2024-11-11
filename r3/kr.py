import RPi.GPIO as GPIO
import time
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



# Set Row pins as output
GPIO.setup(ROW_1, GPIO.OUT)
GPIO.setup(ROW_2, GPIO.OUT)
GPIO.setup(ROW_3, GPIO.OUT)
GPIO.setup(ROW_4, GPIO.OUT)

# Set column pins as input and Pulled up high by default
GPIO.setup(COL_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(COL_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(COL_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(COL_4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

cmd_fw_version = b'\x0A\x56\x0D'
cmd_reader_id = b'\x0A\x53\x0D'
cmd_Q_EPC = b'\x0A\x51\x0D'
cmd_MQ_EPC = b'\x0A\x55\x0D'

# function to read each row and each column
def readRow(line, characters):
    kCmd=""
    GPIO.output(line, GPIO.LOW)
    if(GPIO.input(COL_1) == GPIO.LOW):
        kCmd=characters[0]
    if(GPIO.input(COL_2) == GPIO.LOW):
        kCmd=characters[1]
    if(GPIO.input(COL_3) == GPIO.LOW):
        kCmd=characters[2]
    if(GPIO.input(COL_4) == GPIO.LOW):
        kCmd=characters[3]
    GPIO.output(line, GPIO.HIGH)
    print(kCmd)
    if(kCmd=="S1"):
        print("S1")
        ser.write(cmd_reader_id)
        time.sleep(1)            
        x = ser.readline(1024).rstrip()
        print("Data = ",x)            
        time.sleep(1)
    elif(kCmd=="S2"):
        print("S2")
        ser.write(cmd_fw_version)
        time.sleep(1)            
        x = ser.readline(1024).rstrip()
        print("Data = ",x)            
        time.sleep(1)            
    elif(kCmd=="S3"):
        print("S3")
        ser.write(cmd_Q_EPC)
        time.sleep(1)            
        x = ser.readline(1024).rstrip()
        print("Data = ",x)            
        time.sleep(1)            
    elif(kCmd=="S4"):
        print("S4")
        ser.write(cmd_MQ_EPC)
        time.sleep(1)            
        x = ser.readline(1024).rstrip()
        print("Data = ",x)            
        time.sleep(1)       
"""
         
        case "S5":
            print("S5")
        case "S6":
            print("S6")
        case "S7":
            print("S7")
        case "S8":
            print("S8")
        case "S9":
            print("S9")
        case "S10":
            print("S10")
        case "S11":
            print("S11")
        case "S12":
            print("S12")        
        case "S13":
            print("S13")       
        case "S14":
            print("S14")        
        case "S15":
            print("S15")        
        case "S16":
            print("S16")
        case _:
            print("No op")
"""    

# Endless loop by checking each row 
try:
    while True:
        readRow(ROW_1, ["S4","S3","S2","S1"])
        readRow(ROW_2, ["S8","S7","S6","S5"])
        readRow(ROW_3, ["S12","S11","S10","S9"])
        readRow(ROW_4, ["S16","S15","S14","S13"])
        time.sleep(1) # adjust this per your own setup
except KeyboardInterrupt:
    print("\nKeypad Application Interrupted!")
    GPIO.cleanup()
