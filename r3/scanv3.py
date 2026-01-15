import time
import RPi.GPIO as GPIO
import sys
import serial
import os, json
import requests

from dotenv import load_dotenv

import telepot
from telepot.loop import MessageLoop


# โหลดค่า environment จากไฟล์ .env
load_dotenv()

APISERVER = os.getenv("APISERVER")
key = os.getenv("key")

#telegram 
bot_token = os.getenv("bot_token")
bot_id = os.getenv("bot_id")

clear = lambda: os.system('clear')

RFID_EN_PIN = 4

GPIO.setwarnings(False)

# BCM numbering
GPIO.setmode(GPIO.BCM)

GPIO.setup(RFID_EN_PIN, GPIO.OUT)
GPIO.output(RFID_EN_PIN, GPIO.HIGH)

port = '/dev/ttyAMA0'
#port = '/dev/ttyS0'

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

global Items 
global INV


def sendmessage(text):
    url = "https://api.telegram.org/bot" + bot_token + "/sendMessage?chat_id=" + bot_id + "&text=" + text    
    response = requests.get(url) 
    print(url,' ',response)


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
    timeout = time.time() + 50      #timeout 50 second
    while True:
        ser.write(cmd_MQ_EPC)
        #time.sleep(0.1)     
        time.sleep(0.05)
        while ser.inWaiting() > 0:
            x = ser.readline().strip().decode("utf-8")
            #x = ser.readline()
            #EPC GEN2 ขึ้นต้นด้วย E2
            print(x)
            idx = x.find('E2')
            if idx != -1 and len(x)>28:
                x = x[-8:]
                #print(x)
                #if x not in Items and len(x)>=33 and x.startswith("300",1,4):
                #เก็บเฉพาะ 8 หลักสุดท้ายเพื่อประหยัดพื้นที่
                if x not in Items and len(x)==8:
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
        


try:
    #init cmd
    sendmessage("Start RFID")
    Items=[]
    sys_cmd(cmd_Reader_Power_Max)
    #sys_cmd(cmd_Reader_Power_Min)
    #sys_cmd(cmd_Reader_Power_Mid)

    run_cmd1(cmd_fw_version)
    run_cmd1(cmd_reader_id)

    #Get_One_Item()
    Get_N_Items(100) 
    print(len(Items),' items = ',Items)

    with open("output.txt", "w", encoding="utf-8") as file:
        for item in Items:
            file.write(item + "\n")

    ser.reset_input_buffer()

    '''
    print("Press buttons on your keypad. Ctrl+C to exit.")
    while True:
        time.sleep(1)
    '''        
except KeyboardInterrupt:
    print("Goodbye")
finally:
    print("Finally")
