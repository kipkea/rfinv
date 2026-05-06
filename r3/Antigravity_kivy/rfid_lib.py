import time
import sys
import argparse
import threading
import platform

IS_RPI = platform.system() == 'Linux'

if IS_RPI:
    import RPi.GPIO as GPIO
    import serial


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


if IS_RPI:
    RFID_EN_PIN = 4
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RFID_EN_PIN, GPIO.OUT)
    GPIO.output(RFID_EN_PIN, GPIO.HIGH)

    port = '/dev/ttyAMA0'
    buadrate = 38400

    #only setting 
    def sys_cmd(ser, CMD):
        ser.write(CMD)
        #time.sleep(2)     
        ser.reset_input_buffer()

    def rfcmd(ser, cmd_str):
        # คำสั่งต้องขึ้นต้นด้วย LF (0x0A) และจบด้วย CR (0x0D) [9]
        full_cmd = b'\x0A' + cmd_str.encode() + b'\x0D'
        ser.write(full_cmd)

    #ตั้งค่า
    ser = serial.Serial(port,buadrate,8)
    ser.port = port
    ser.baudrate = buadrate
    time.sleep(1)

    #เปลี่ยนความเร็วเป็น 230400
    rfcmd(ser,"NA,7")
    time.sleep(0.2)
    ser.close()

    #เชื่อมต่อใหม่
    bouadrate = 230400
    ser = serial.Serial(port,bouadrate,8)
    ser.port = port
    ser.baudrate = bouadrate
    time.sleep(0.2)

    sys_cmd(ser, cmd_Reader_Power_Max)
else:
    ser = None

class RFCounter:
    def __init__(self, target_count=1):
        self.target_count = target_count
        self.current_count = 0
        self.start_time = None
        self.end_time = None
        self.scanned_data = []
        self.count_cmd_loop = 0
        self.is_running = False

    def run(self):
        #         """เริ่มการทำงานของโปรแกรม"""
        print(f"--- เตรียมพร้อม: ต้องการข้อมูลจำนวน {self.target_count} รายการ ---")
        print(">>> กรุณาเริ่มอ่าน RFID Tag ได้เลย...")
        code = ""
        
        try:
            while self.current_count < self.target_count:          
                # รอรับข้อมูล (โปรแกรมจะหยุดรอตรงนี้จนกว่าจะมีการยิงและส่ง Enter)
                #code = input() 
                if not IS_RPI:
                    time.sleep(1)
                    continue

                ser.reset_output_buffer()
                #print("Send command : ",cmd_MQ_EPC)
                #MQ_EPC อ่านหลายแท็กพร้อมกัน
                ser.write(cmd_MQ_EPC)
                time.sleep(0.1)     
                #time.sleep(0.01)
                
                try:
                    # 2. อ่านข้อมูล Response
                    while True:
                        if ser.in_waiting > 0:
                            try:
                                # อ่านข้อมูลจนจบLine (<LF>) [4]
                                raw_line = ser.read_until(b'\x0A')
                                #print("Raw Line: ", raw_line)
                                line = raw_line.decode('ascii', errors='ignore').strip()

                                # ถ้าเป็น 'U' ตัวเดียว คือจบ Batch รอบนี้
                                if len(line) == 1:
                                    break 
                                
                                idx = line.find('E2')
                                if idx != -1 and len(line)>28:
                                    x = line[-8:]
                                    #print(x)
                                    #if x not in Items and len(x)>=33 and x.startswith("300",1,4):
                                    #เก็บเฉพาะ 8 หลักสุดท้ายเพื่อประหยัดพื้นที่                       
                                    #code = x  

                                    #เก็บทั้งหมดไว้ก่อน แล้วค่อยตัดทีหลังถ้าต้องการข้อมูลเฉพาะส่วน
                                    code = line  
                                    print(code)                    
                                    
                                # เริ่มจับเวลาเมื่อข้อมูลแรกเข้ามา
                                self.count_cmd_loop += 1
                                if self.current_count == 0:
                                    self.start_time = time.perf_counter()
                                    #print(f"--> เริ่มจับเวลา! (อ่านครั้งแรก: {code})")
                                
                                #if code not in self.scanned_data and len(code)==8:            
                                if code not in self.scanned_data:            
                                    self.current_count += 1
                                    self.scanned_data.append(code)
                                    
                                    # แสดงผลความคืบหน้า
                                    print(f"[{self.current_count}/{self.target_count}] รับข้อมูล: {code}")                                        
                                        
                            except UnicodeDecodeError:
                                pass
            
                except EOFError:
                    break

                if not code:
                    continue  # ข้ามถ้าเป็นค่าว่าง
                                    
                # หน่วงเวลาเล็กน้อยระหว่างรอบคำสั่ง U เพื่อไม่ให้ Buffer เต็ม
                time.sleep(0.01)
            # จบการทำงานเมื่อครบจำนวน
            self.end_time = time.perf_counter()
            #self.show_summary()

        except KeyboardInterrupt:
            print("\n\n[!] ยกเลิกการทำงานโดยผู้ใช้")

    def start_scan(self, callback=None):
        """เริ่มอ่านข้อมูลแบบวนลูป (ใช้ Thread เพื่อไม่ให้ UI ค้าง)"""
        self.is_running = True
        self.scanned_data = []
        self.current_count = 0
        self.start_time = time.perf_counter()
        if IS_RPI:
            threading.Thread(target=self._scan_thread, args=(callback,), daemon=True).start()
        else:
            print("Running on Windows/Mac - RFID Scanner disabled.")
        
    def stop_scan(self):
        """หยุดการอ่านข้อมูล"""
        self.is_running = False
        self.end_time = time.perf_counter()

    def _scan_thread(self, callback):
        print("--- เริ่มการอ่าน RFID แบบต่อเนื่อง ---")
        while self.is_running:
            ser.reset_output_buffer()
            ser.write(cmd_MQ_EPC)
            time.sleep(0.1)
            try:
                while self.is_running:
                    if ser.in_waiting > 0:
                        raw_line = ser.read_until(b'\x0A')
                        line = raw_line.decode('ascii', errors='ignore').strip()
                        if len(line) == 1:
                            break 
                        idx = line.find('E2')
                        if idx != -1 and len(line) > 28:
                            code = line  
                            self.count_cmd_loop += 1
                            if code not in self.scanned_data:            
                                self.current_count += 1
                                self.scanned_data.append(code)
                                print(f"รับข้อมูลใหม่: {code}")
                                if callback:
                                    callback(code)
                    else:
                        break
            except Exception:
                pass
            time.sleep(0.01)

    def show_summary(self):
        """คำนวณและแสดงผลลัพธ์"""
        if self.start_time and self.end_time:
            total_time = self.end_time - self.start_time
            avg_time = total_time / self.target_count
            
            print("\n" + "="*40)
            print(f"   สรุปผลการทำงาน (ครบ {self.target_count} รายการ)")
            print("="*40)
            print(f"เวลาทั้งหมดที่ใช้ : {total_time:.6f} วินาที")
            print(f"ความเร็วเฉลี่ย    : {avg_time:.6f} วินาที/รายการ")
            print(f"ใช้คำสั่งทั้งหมด    : {self.count_cmd_loop} ครั้ง")
            print("="*40)
        else:
            print("\nยังไม่มีข้อมูลเพียงพอสำหรับการคำนวณ")
