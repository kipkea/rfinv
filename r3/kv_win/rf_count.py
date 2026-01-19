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
       

class RFCounter:
    def __init__(self, target_count):
        self.target_count = target_count
        self.current_count = 0
        self.start_time = None
        self.end_time = None
        self.scanned_data = []

    def run(self):
        """เริ่มการทำงานของโปรแกรม"""
        print(f"--- เตรียมพร้อม: ต้องการข้อมูลจำนวน {self.target_count} รายการ ---")
        print(">>> กรุณาเริ่มอ่าน RFID Tag ได้เลย...")
        code = ""
        
        try:
            while self.current_count < self.target_count:          
                # รอรับข้อมูล (โปรแกรมจะหยุดรอตรงนี้จนกว่าจะมีการยิงและส่ง Enter)
                #code = input() 
                ser.reset_output_buffer()
                #print("Send command : ",cmd_MQ_EPC)

                ser.write(cmd_MQ_EPC)
                #time.sleep(0.1)     
                time.sleep(0.05)
                
                try:
                    while ser.inWaiting() > 0:
                        x = ser.readline().strip().decode("utf-8")
                        #x = ser.readline()
                        #EPC GEN2 ขึ้นต้นด้วย E2
                        #print(x)
                        idx = x.find('E2')
                        if idx != -1 and len(x)>28:
                            x = x[-8:]
                            #print(x)
                            #if x not in Items and len(x)>=33 and x.startswith("300",1,4):
                            #เก็บเฉพาะ 8 หลักสุดท้ายเพื่อประหยัดพื้นที่                       
                            code = x        
                                                
                except EOFError:
                        break

                if not code:
                    continue  # ข้ามถ้าเป็นค่าว่าง


                # เริ่มจับเวลาเมื่อข้อมูลแรกเข้ามา
                if self.current_count == 0:
                    self.start_time = time.perf_counter()
                    print(f"--> เริ่มจับเวลา! (อ่านครั้งแรก: {code})")
                
                if code not in self.scanned_data and len(code)==8:            
                    self.current_count += 1
                    self.scanned_data.append(code)
                    
                    # แสดงผลความคืบหน้า
                    print(f"[{self.current_count}/{self.target_count}] รับข้อมูล: {code}")

            # จบการทำงานเมื่อครบจำนวน
            self.end_time = time.perf_counter()
            self.show_summary()

        except KeyboardInterrupt:
            print("\n\n[!] ยกเลิกการทำงานโดยผู้ใช้")

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
            print("="*40)
        else:
            print("\nยังไม่มีข้อมูลเพียงพอสำหรับการคำนวณ")

if __name__ == "__main__":
# --- ส่วนที่แก้ไข: รับค่า N จาก Command Line ---
    
    # ค่าเริ่มต้น (เผื่อกรณีไม่ได้ใส่ parameter มา)
    default_n = 1 
    target_n = default_n

    # ตรวจสอบว่ามีการส่ง parameter มาหรือไม่
    # sys.argv[0] คือชื่อไฟล์ script, sys.argv[1] คือ parameter ตัวแรก
    if len(sys.argv) > 1:
        try:
            # แปลงค่าที่รับมาเป็นตัวเลขจำนวนเต็ม (Integer)
            target_n = int(sys.argv[1])
            
            if target_n <= 0:
                print("Error: กรุณาใส่จำนวนเต็มที่มากกว่า 0")
                sys.exit(1)
                
        except ValueError:
            print(f"Error: '{sys.argv[1]}' ไม่ใช่ตัวเลข กรุณาใส่จำนวนเต็ม")
            sys.exit(1)
    else:
        print(f"Warning: ไม่ได้ระบุจำนวน N มา จะใช้ค่าเริ่มต้น = {default_n}")
        print("Usage: python3 rf_count.py <จำนวนที่ต้องการ>")
        print("-" * 40)
        
    # เริ่มต้นการทำงาน
    app = RFCounter(target_n)
    app.run()