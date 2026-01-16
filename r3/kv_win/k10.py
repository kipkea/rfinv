from kivy.app import App
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.window import Window
import cv2
import numpy as np

# ส่วนตรวจสอบว่าเป็น Raspberry Pi หรือไม่
try:
    from picamera2 import Picamera2
    USING_RPI = True
    print("NovaLab: Detected Raspberry Pi 5 - Using Picamera2 Native")
except ImportError:
    USING_RPI = False
    print("NovaLab: Detected PC/Other - Using standard OpenCV")

class HybridCamApp(App):
    def build(self):
        self.img1 = Image()
        
        # --- ส่วนตั้งค่ากล้อง ---
        if USING_RPI:
            # ตั้งค่า Picamera2 สำหรับ Pi 5
            self.picam2 = Picamera2()
            # config ความละเอียด (ลดลงเพื่อความลื่นไหล)
            config = self.picam2.create_configuration(main={"size": (640, 480), "format": "RGB888"})
            self.picam2.configure(config)
            self.picam2.start()
        else:
            # ตั้งค่า OpenCV สำหรับ PC
            self.capture = cv2.VideoCapture(0)
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # สั่งอัปเดตหน้าจอ 30 ครั้งต่อวินาที (30 FPS)
        Clock.schedule_interval(self.update, 1.0 / 30.0)
        return self.img1

    def update(self, dt):
        frame = None
        
        # 1. ดึงภาพ (ตาม Hardware)
        if USING_RPI:
            # ดึงภาพจาก Pi 5 (จะได้เป็น RGB มาเลย ไม่ต้องแปลง BGR)
            # wait=False คือถ้าภาพไม่มาไม่ต้องรอ (กันจอค้าง)
            try:
                frame = self.picam2.capture_array()
            except Exception as e:
                print(f"Frame Error: {e}")
        else:
            # ดึงภาพจาก PC (OpenCV)
            ret, temp_frame = self.capture.read()
            if ret:
                # OpenCV ให้มาเป็น BGR ต้องแปลงเป็น RGB เพื่อให้สีตรงกับ Kivy
                frame = cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB)
                # กลับหัวภาพ (OpenCV มักกลับหัว)
                frame = cv2.flip(frame, 0)

        # 2. แปลงเป็น Texture แสดงผล
        if frame is not None:
            # สร้าง Texture ให้ Kivy
            # bufferfmt='ubyte' คือข้อมูล 8-bit (0-255) มาตรฐาน
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
            texture.blit_buffer(frame.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
            
            # ถ้าเป็น Pi บางทีภาพจะกลับหัว ให้แก้ตรงนี้
            if USING_RPI:
                self.img1.texture = texture # หรือ texture.flip_vertical() ถ้าภาพกลับหัว
            else:
                self.img1.texture = texture

    def on_stop(self):
        # คืนค่ากล้องเมื่อปิดโปรแกรม
        if USING_RPI:
            self.picam2.stop()
        else:
            self.capture.release()

if __name__ == '__main__':
    HybridCamApp().run()