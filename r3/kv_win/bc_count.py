import time
import sys

class BarcodeCounter:
    def __init__(self, target_count):
        self.target_count = target_count
        self.current_count = 0
        self.start_time = None
        self.end_time = None
        self.scanned_data = []

    def run(self):
        """เริ่มการทำงานของโปรแกรม"""
        print(f"--- เตรียมพร้อม: ต้องการข้อมูลจำนวน {self.target_count} รายการ ---")
        print(">>> กรุณาเริ่มยิงบาร์โค้ดได้เลย...")

        try:
            while self.current_count < self.target_count:
                # รับข้อมูลจาก Barcode Scanner (เหมือนรับจากคีย์บอร์ด)
                # ใช้ sys.stdin.readline จะจัดการ Buffer ได้ดีกว่า input() เล็กน้อยในงานลักษณะนี้
                # แต่ input() ก็ใช้ได้เช่นกัน
                
                try:
                    # รอรับข้อมูล (โปรแกรมจะหยุดรอตรงนี้จนกว่าจะมีการยิงและส่ง Enter)
                    code = input() 
                except EOFError:
                    break

                if not code.strip():
                    continue  # ข้ามถ้าเป็นค่าว่าง

                # เริ่มจับเวลาเมื่อข้อมูลแรกเข้ามา
                if self.current_count == 0:
                    self.start_time = time.perf_counter()
                    print(f"--> เริ่มจับเวลา! (ยิงครั้งแรก: {code})")
                
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
    
    # เริ่มต้นการทำงาน
    app = BarcodeCounter(target_n)
    app.run()