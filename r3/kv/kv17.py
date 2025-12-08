import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
import subprocess
import json
import os
import time

kivy.require('2.1.0') # ตรวจสอบเวอร์ชัน Kivy

# กำหนดชื่อไฟล์ Config
CONFIG_FILE = 'rpicam_config.json'
# กำหนดชื่อไฟล์รูปภาพ
IMAGE_PATH = '/home/pi/Pictures/rpicam_'

class CameraControl(BoxLayout):
    """Class หลักสำหรับควบคุม GUI และ Logic"""
    
    # Kivy Properties ที่เชื่อมโยงกับ Widgets ในไฟล์ .kv
    hflip_active = ObjectProperty(False)
    vflip_active = ObjectProperty(False)
    rotation_value = StringProperty("0")
    contrast_value = StringProperty("1.0")
    saturation_value = StringProperty("1.0")
    width_value = StringProperty("1920")
    height_value = StringProperty("1080")
    status_text = StringProperty("สถานะ: พร้อมใช้งาน")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_config() # โหลดการตั้งค่าเมื่อเริ่มต้น
        self.preview_process = None # ตัวแปรสำหรับเก็บ process ของ rpicam-hello

    def load_config(self):
        """โหลดการตั้งค่าจากไฟล์ JSON"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    
                    # อัปเดต Properties จาก config
                    self.hflip_active = config.get('hflip', False)
                    self.vflip_active = config.get('vflip', False)
                    self.rotation_value = str(config.get('rotation', 0))
                    self.contrast_value = str(config.get('contrast', 1.0))
                    self.saturation_value = str(config.get('saturation', 1.0))
                    self.width_value = str(config.get('width', 1920))
                    self.height_value = str(config.get('height', 1080))
                    
                    self.status_text = f"สถานะ: โหลดการตั้งค่าจาก {CONFIG_FILE} สำเร็จ"
            except Exception as e:
                self.status_text = f"สถานะ: Error ในการโหลด Config: {e}"
        else:
            self.status_text = "สถานะ: ไม่พบไฟล์ Config ใช้ค่าเริ่มต้น"

    def save_config(self):
        """บันทึกการตั้งค่าปัจจุบันลงในไฟล์ JSON"""
        config = {
            'hflip': self.hflip_active,
            'vflip': self.vflip_active,
            'rotation': int(self.rotation_value),
            'contrast': float(self.contrast_value),
            'saturation': float(self.saturation_value),
            'width': int(self.width_value),
            'height': int(self.height_value)
        }
        
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            self.status_text = f"สถานะ: บันทึก Config ลง {CONFIG_FILE} สำเร็จ"
        except Exception as e:
            self.status_text = f"สถานะ: Error ในการบันทึก Config: {e}"

    def build_command_args(self, base_command="libcamera-hello"):
        """สร้างรายการคำสั่ง (Arguments List) จากการตั้งค่าใน GUI"""
        
        args = [base_command]
        
        # 1. การหมุน/กลับด้าน
        if self.hflip_active:
            args.append("--hflip")
        if self.vflip_active:
            args.append("--vflip")
        
        rotation = int(self.rotation_value)
        if rotation in [90, 180, 270]:
             args.extend(["--rotation", str(rotation)])

        # 2. การปรับภาพ/สี
        args.extend(["--contrast", self.contrast_value])
        args.extend(["--saturation", self.saturation_value])
        
        # 3. ขนาดภาพ (สำหรับ libcamera-still)
        if base_command == "libcamera-still":
            args.extend(["--width", self.width_value, "--height", self.height_value])
            # ตั้งค่าให้ rpicam-hello รันเป็นเวลา 0.1 วินาทีแล้วปิดตัวเอง (สำหรับ Preview)
        elif base_command == "libcamera-hello":
            args.extend(["--fullscreen", "--display", "0", "--qt-preview"]) # เปิด Fullscreen และใช้ Qt Preview
            args.append("--timeout")
            args.append("0") # ใช้ 0 เพื่อให้โปรแกรมรันไปเรื่อย ๆ จนกว่าจะถูกปิด

        return args

    def start_preview(self):
        """เริ่มรัน Preview ด้วย libcamera-hello"""
        self.stop_preview() # ปิด Preview เก่าก่อน
        
        # ใช้ libcamera-hello สำหรับ Preview
        args = self.build_command_args("libcamera-hello")
        
        try:
            self.status_text = f"สถานะ: เริ่ม Preview ด้วยคำสั่ง: {' '.join(args)}"
            # รันเป็น subprocess เพื่อไม่ให้บล็อก GUI
            self.preview_process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # เราต้องหาทางฆ่า process นี้เมื่อผู้ใช้ต้องการหยุด
            
        except FileNotFoundError:
            self.status_text = "ERROR: ไม่พบ 'libcamera-hello' ตรวจสอบการติดตั้ง libcamera"
        except Exception as e:
            self.status_text = f"ERROR: ไม่สามารถเริ่ม Preview: {e}"

    def stop_preview(self):
        """หยุดรัน Preview"""
        if self.preview_process:
            self.preview_process.terminate() # สั่ง terminate process
            self.preview_process.wait() # รอจนกว่าจะปิดสนิท
            self.preview_process = None
            self.status_text = "สถานะ: หยุด Preview แล้ว"
            
    def capture_image(self):
        """ถ่ายภาพนิ่งด้วย libcamera-still"""
        self.stop_preview() # หยุด Preview ก่อนถ่ายภาพ เพื่อให้ libcamera-still เข้าถึงกล้องได้
        
        # ใช้ libcamera-still สำหรับถ่ายภาพ
        args = self.build_command_args("libcamera-still")
        
        # เพิ่มชื่อไฟล์สำหรับบันทึก
        filename = f"{IMAGE_PATH}{time.strftime('%Y%m%d_%H%M%S')}.jpg"
        args.extend(["-o", filename])
        
        try:
            self.status_text = f"สถานะ: กำลังถ่ายภาพด้วยคำสั่ง: {' '.join(args)}"
            # รันแบบ Wait เพื่อรอจนกว่าภาพจะถูกบันทึกเสร็จ
            result = subprocess.run(args, capture_output=True, text=True, check=True)
            
            self.status_text = f"สถานะ: ถ่ายภาพสำเร็จ: {filename}"
            # แสดง Pop-up แจ้งเตือน
            popup = Popup(title='ถ่ายภาพสำเร็จ',
                          content=Label(text=f'บันทึกที่:\n{filename}'),
                          size_hint=(0.8, 0.4))
            popup.open()
            
        except subprocess.CalledProcessError as e:
            self.status_text = f"ERROR: การถ่ายภาพล้มเหลว: {e.stderr.strip()}"
        except FileNotFoundError:
            self.status_text = "ERROR: ไม่พบ 'libcamera-still' ตรวจสอบการติดตั้ง libcamera"
        except Exception as e:
            self.status_text = f"ERROR: ไม่สามารถถ่ายภาพ: {e}"
        finally:
             self.start_preview() # เริ่ม Preview ใหม่หลังจากถ่ายภาพเสร็จ

class RPiCamApp(App):
    def build(self):
        return CameraControl()

if __name__ == '__main__':
    RPiCamApp().run()