import time
import sys
import RPi.GPIO as GPIO
import serial

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


def rfcmd(cmd_str):
    # คำสั่งต้องขึ้นต้นด้วย LF (0x0A) และจบด้วย CR (0x0D) [9]
    full_cmd = b'\x0A' + cmd_str.encode() + b'\x0D'
    ser.write(full_cmd)
    
    
ser = serial.Serial(port,buadrate,8)
ser.port = port
ser.baudrate = buadrate
time.sleep(0.2)

#เปลี่ยนความเร็วเป็น 230400
rfcmd("NA,7")
time.sleep(0.2)
ser.close()

#เชื่อมต่อใหม่
bouadrate = 230400
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

#only setting 
def sys_cmd(CMD):
    ser.write(CMD)
    #time.sleep(2)     
    ser.reset_input_buffer()


sys_cmd(cmd_Reader_Power_Max)
#sys_cmd(cmd_Reader_Power_Min)
#sys_cmd(cmd_Reader_Power_Mid)

#set power read       
rfcmd("N1,1B")   #set power read to max 25 db
time.sleep(0.2)


# สมมติว่าสร้าง set ไว้เก็บ UID ที่ไม่ซ้ำกัน
scanned_tags = set()
current_count = 0
target_tag_count = 10

# 5. ลูปอ่าน Tag อย่างต่อเนื่อง
try:
    while current_count < target_tag_count:
        # ส่งคำสั่งอ่าน Multi-Tag (U)
        rfcmd("U")
        time.sleep(0.5)
        
        # อ่านข้อมูลที่ไหลเข้ามา
        # ข้อมูลตอบกลับจะเริ่มด้วย LF และจบด้วย CR LF [9], [10]
        if ser.in_waiting > 0:
        
            response = ser.read_until(b'\x0D\x0A') 
            if len(response) > 20:
                print("Response Raw: ",response)
                try:
                    # แปลงข้อมูลและกรองเฉพาะบรรทัดที่เป็นข้อมูล Tag (มักขึ้นต้นด้วย U)
                    decoded_data = response.decode('ascii', errors='ignore').strip()
                    if decoded_data.startswith('U'):
                        # ตัดตัวอักษร U นำหน้าออกเพื่อให้ได้ EPC [3]
                        epc_data = decoded_data[1:]
                        print(f"Tag Found: {epc_data}")
                        
                        # ตรวจสอบรูปแบบข้อมูล (เช่น ต้องมี E2 และความยาวเหมาะสม)
                        idx = epc_data.find('E2')
                        if idx != -1 and len(epc_data) > 28:
                            # สกัดเอาเฉพาะรหัส EPC (ตัวอย่างนี้เอา 8 หลักสุดท้ายตามเดิม)
                            tag_id = epc_data[-8:]
                            
                            # ตรวจสอบว่ายังไม่เคยอ่านแท็กนี้ในรอบนี้
                            if tag_id not in scanned_tags:
                                scanned_tags.add(tag_id)
                                current_count = len(scanned_tags)
                                print(f"Found new tag: {tag_id} | Total: {current_count}")
                                
                            if current_count >= target_tag_count:
                                break                    
                except Exception as e:
                    pass
except KeyboardInterrupt:
    ser.close()