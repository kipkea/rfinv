from pad4pi import rpi_gpio
import time
import RPi.GPIO as GPIO
import sys
import serial
import os, json
import requests

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

global Items 

#API key for KeaPC is: 8yArxdsF.E4viD1uo4yLSibw0QqI5Vno4KPJ6b8hO
#API key for keaCom is: swQuMMgt.vh1nQPMnHmNtClcTQM5DOcpjhHv4X0RA
 
#dev
url="http://10.35.117.143:8000/api/basic/"
key = "vaGkQQur.OkotzgLTEDFuXwzZrUA1oMUH7iKWDugW"
#API key for keaCom is: swQuMMgt.vh1nQPMnHmNtClcTQM5DOcpjhHv4X0RA
key = "swQuMMgt.vh1nQPMnHmNtClcTQM5DOcpjhHv4X0RA"
#API Key for PI3
key = "TM4fc8ew.yIeDMRVam9qvQvyGr68n3EpXirAdwv5h"

#aws
#url="http://ec2-52-20-131-209.compute-1.amazonaws.com/api/basic/"
#key = "fS6yn9J2.V0nZcnDAG5Jf6uZHafXQa3R1a2aqSJbe"

#APISERVER = "192.168.1.5:8000"
APISERVER = "ec2-52-20-131-209.compute-1.amazonaws.com"

def Api_Call(URL):
    cmd="curl -s -k -H Authorization: Api-Key " + key + " " + URL
    print (URL)

    headers = {'x-api-key':key}
    #print(headers)

    resp = requests.get(URL,headers=headers)
    #print(resp.status_code)
    #print(resp.text)
    if resp.status_code == 200:
        jData = resp.json()
        #print(jData)
        print(json.dumps(jData, indent=4, sort_keys=True))
        for item in jData:
            print(item) 
    else:
        print(f"Error: {resp.status_code}")

def Api_Call_POST(URL,data):
    cmd="curl -s -k -H Authorization: Api-Key " + key + " " + URL
    print (URL)
    print(data)

    headers = {'x-api-key':key}

    #resp = requests.post(URL, json=data)
    resp = requests.post(URL, data=data, headers=headers)

    if resp.status_code == 201:
        print("POST successfully")
    else:
        print(f"Error: {resp.status_code}")
 
def sys_cmd(CMD):
    ser.write(CMD)
    time.sleep(1)     

def run_cmd1(CMD):
    global Items
    print("Send command : ",CMD)
    ser.write(CMD)
    time.sleep(1)     
    while ser.inWaiting() > 0:
        print(ser.readline().strip())
    ser.reset_input_buffer()

def run_cmd(CMD):
    global Items
    print("Send command : ",CMD)
    ser.write(CMD)
    time.sleep(1)     
    while ser.inWaiting() > 0:
        x = ser.readline().rstrip()
        if x not in Items and len(x)>10:
            Items.append(x)
            print("Items ",len(Items),' is ',x)
    ser.reset_input_buffer()

def run_cmd2(CMD):
    print("Send command : ",CMD)
    while True:
        ser.write(CMD)
        time.sleep(0.1)     
        while ser.inWaiting() > 0:
            x = ser.readline().rstrip()
            if x not in Items and len(x)>10:
                Items.append(x)
                print("Items ",len(Items),' is ',x)

def print_key(key):
    global Items
    print(f"Received key from interrupt:: {key}")
    match key:
        case 13:
            #หมายเลข firmware
            print("FW Version?")
            run_cmd1(cmd_fw_version)
        case 9:
            #หมายเลขเครื่องอ่าน
            print("Reader ID?")
            run_cmd1(cmd_reader_id)
        case 5:
            #อ่าน 1 รายการ
            print("Read 1 item")
            run_cmd(cmd_Q_EPC)
        case 1:
            #อ่านเป็นชุด loop
            print("Read Multi Items <inf loop>")
            run_cmd2(cmd_MQ_EPC)
        case 6:
            #อ่านเป็นชุด
            print("Read Multi Items")
            run_cmd(cmd_MQ_EPC)  
        case 15:
            #reset items
            Items = []
            print("Reset items")
        case 11:
            #List items
            print(len(Items),' items = ',Items)
        case 16:
            print("exit program")
            sys.exit(0)
        case 12:
            print("List ALL RFID")
            url="http://"+APISERVER+"/api/basic/"
            Api_Call(url)
        case 14:
            print("List ALL Asset")
            url="http://"+APISERVER+"/api/inventorys/"
            Api_Call(url)          
        case 7:
            print("Add New RFID")
            url = "http://"+APISERVER+"/api/rfidtags/"
            #Loop Items
            for item in Items:
                data = {"RFID": item, "is_location": False, "recorded_by":1}
                Api_Call_POST(url,data=data)

        case _:
            print("No Command")


try:
    #init cmd
    Items=[]
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