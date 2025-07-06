from pad4pi import rpi_gpio
import time
import RPi.GPIO as GPIO
import sys
import serial
import os, json
import requests

import telepot
from telepot.loop import MessageLoop


clear = lambda: os.system('clear')

RFID_EN_PIN = 4

GPIO.setwarnings(False)

# BCM numbering
GPIO.setmode(GPIO.BCM)

GPIO.setup(RFID_EN_PIN, GPIO.OUT)
GPIO.output(RFID_EN_PIN, GPIO.HIGH)

port = '/dev/ttyAMA0'   #r5
#port = '/dev/ttyS0'    #r3

buadrate = 38400
#buadrate = 57600
#buadrate = 115200

ser = serial.Serial(port,buadrate,8)
ser.port = port
ser.baudrate = buadrate
time.sleep(0.2)

cmd_fw_version = b'\x0A\x56\x0D'    #<LF>V<CR>
cmd_reader_id = b'\x0A\x53\x0D'     #<LF>S<CR>
cmd_Q_EPC = b'\x0A\x51\x0D'         #<LF>Q<CR>
cmd_MQ_EPC = b'\x0A\x55\x0D'        #<LF>U<CR>
#read power 00 - 1B 27 level -2 to 25 db
#0A 4E 30 2C 30 30 0D -- -2         #<LF>N0,00<CR>
#0A 4E 30 2C 31 42 0D -- 25         #<LF>N0,1B<CR>

cmd_Reader_Power_Max = b'\x0A\x4E\x30\x2C\x31\x42\x0D'
cmd_Reader_Power_Mid = b'\x0A\x4E\x30\x2C\x30\x0F\x0D'
cmd_Reader_Power_Min = b'\x0A\x4E\x30\x2C\x30\x30\x0D'

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
global INV


#dev
APISERVER = "192.168.1.7:8000"
key = "TM4fc8ew.yIeDMRVam9qvQvyGr68n3EpXirAdwv5h"

#aws
#APISERVER = "ec2-52-20-131-209.compute-1.amazonaws.com"
#key = "cW0QbZy6.mQyu31pBYPbsQomB8GKQwGuVBqnGs0aP"

#telegram 
bot_token = '7896527649:AAHEKeT7XblXaeT5o1dBAK11ERYfiHK9BM0'
bot_id = '5595830319'

#Get call
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

#Post Call
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
 
#only setting 
def sys_cmd(CMD):
    ser.write(CMD)
    #time.sleep(2)     
    ser.reset_input_buffer()

#only display result
def run_cmd1(CMD):
    ser.reset_output_buffer()
    print("Send command : ",CMD)
    ser.write(CMD)
    time.sleep(0.1)     
    while ser.inWaiting() > 0:
        print(ser.readline().strip().decode("utf-8"))
        #print(ser.readline())
    ser.reset_input_buffer()

#Collect 1 Item
def Get_One_Item():
    global Items
    ser.reset_output_buffer()
    print("Send command : ",cmd_Q_EPC)
    ser.write(cmd_Q_EPC)
    #time.sleep(0.1)     
    while ser.inWaiting() > 0:
        x = ser.readline().strip().decode("utf-8")
        #x = ser.readline()
        print(x)
        if x not in Items and len(x)>=33 and x.startswith("300",1,4):
            Items.append(x)
            print("Items ",len(Items),' is ',x)
            #print("Item added")
    ser.reset_input_buffer()


#Collect Items
def Get_N_Items(N):
    global Items
    ser.reset_output_buffer()
    print("Send command : ",cmd_MQ_EPC)
    timeout = time.time() + 10
    while True:
        ser.write(cmd_MQ_EPC)
        #time.sleep(0.1)     
        while ser.inWaiting() > 0:
            x = ser.readline().strip().decode("utf-8")
            #x = ser.readline()
            print(x)
            if x not in Items and len(x)>=33 and x.startswith("300",1,4):
                Items.append(x)
                print("Items ",len(Items),' is ',x)
                #print("Item added")
        if len(Items)>=N or time.time() > timeout:
            ser.reset_input_buffer()
            break
        
#display remain inv
def List_remain_INV():
    global INV
    clear()
    for item in INV:
        print(item['name'],'-',item['rfid_tag']['RFID'])

#Check all INV
def Check_All_INV():
    global INV

    ser.reset_output_buffer()

    url="http://"+APISERVER+"/api/inventorys/"
    headers = {'x-api-key':key}
    #print(headers)

    resp = requests.get(url,headers=headers)
    if resp.status_code == 200:
        INV = resp.json()
    else:
        print(f"Error: {resp.status_code}")    

    List_remain_INV()

    start_time = time.time()
    timeout = time.time() + 15  #15 second
    while True:
        ser.write(cmd_MQ_EPC)
        #time.sleep(0.5)     
        while ser.inWaiting() > 0:
            #x = ser.readline().strip().decode("utf-8")
            x = ser.readline()
            item = x.strip().decode("utf-8")
            #item = x
            #print(item,'-',len(item))
            
            if len(item)>=33 and item.startswith("300",1,4):
                #fix bug
                item = "Q" + item[1:]
                #print("Remove ",item)
                for inv in INV:
                    if inv['rfid_tag']['RFID'] == item:
                        INV.remove(inv)
                        List_remain_INV()

        if len(INV)==0 or time.time() > timeout:
            print("Usage time ",time.time()-start_time," seconds")
            if len(INV)>0:
                print("Time over 15 seconds")
            else:
                print("All asset OK")
            break
        ser.reset_input_buffer()
   


#Check INV & Collect Items
def Chk_INV():
    global Items
    ser.reset_output_buffer()
    start_time = time.time()
    timeout = time.time() + 15  #15 second
    while True:
        ser.write(cmd_MQ_EPC)
        #time.sleep(0.5)     
        while ser.inWaiting() > 0:
            #x = ser.readline().strip().decode("utf-8")
            x = ser.readline()
            item = x.strip().decode("utf-8")
            #item = x
            if item not in Items and len(item)>=33 and item.startswith("300",1,4):
                Items.append(item)
                print("Items add -> ",len(Items),' is ',item)
                #print("Item added")
        if len(Items)>=21 or time.time() > timeout:
            print("Usage time ",time.time()-start_time," seconds")
            if len(Items)<21:
                print("Time over 15 seconds")
            else:
                print("All asset OK")
            break
        ser.reset_input_buffer()

#find info
def Find_INV():
    #read tag
    ser.reset_output_buffer()
    tag_found = 0
    while tag_found == 0:
        ser.write(cmd_Q_EPC)
        #time.sleep(1)     
        while ser.inWaiting() > 0:
            x = ser.readline()
            item = x.strip().decode("utf-8")
            
            if len(item)>=33 and item.startswith("300",1,4):            
                tag_found += 1
                #call api
                url = "http://"+APISERVER+"/api/inv/"+item
                Api_Call(url)

    ser.reset_input_buffer()
        

#interupt call
def print_key(key):
    global Items
    print(f"Received key from interrupt:: {key}")
    match key:
        case 13:
            #หมายเลข firmware
            print("FW Version?")
            sendmessage("FW Version")
            run_cmd1(cmd_fw_version)
        case 9:
            #หมายเลขเครื่องอ่าน
            print("Reader ID?")
            run_cmd1(cmd_reader_id)
        case 5:
            #อ่าน 1 รายการ
            print("Read 1 item")
            Get_One_Item()
        case 1:
            #อ่านเป็นชุด
            print("Read Multi Items")
            Get_N_Items(10) 
        case 15:
            #reset items
            Items = []
            print("Reset items")
        case 11:
            #List items
            print(len(Items),' items = ',Items)
        case 16:
            print("exit program")
            keypad.cleanup()
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
        case 8:
            print("Search TAG")
            Find_INV()
        case 3:
            print("Check INV")
            Chk_INV()
        case 4:
            print("Check INV")
            Check_All_INV()
        case _:
            print("No Command")

def sendmessage(text):
    url = "https://api.telegram.org/bot" + bot_token + "/sendMessage?chat_id=" + bot_id + "&text=" + text    
    response = requests.get(url) 
    print(url,' ',response)
'''
    start = 0
    sendmessage("Starting conversation") 
    while(True):
        url = "https://api.telegram.org/bot" + token + "/getUpdates?offset=" + last
        response = requests.get(url) 
        dict = response.json() 
        result = dict['result'] 
        nummessages = len(result)

        if (nummessages>=1):
            message = result[nummessages -1]['message'] last = result[nummessages -1]['update_id'] text = message['text']
            print(text)

            if ((text==”exit”)and(start>0)): 
                sendmessage(“See you later”) 
                break
        else:
            start = 1
            last = str(last +1)
'''    

try:
    #init cmd
    Items=[]
    sys_cmd(cmd_Reader_Power_Max)
    #sys_cmd(cmd_Reader_Power_Min)
    #sys_cmd(cmd_Reader_Power_Mid)

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
