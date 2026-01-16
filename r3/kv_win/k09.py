from kivy.app import App
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import cv2
import platform

class CamApp(App):
    def build(self):
        self.img1 = Image()
        
        # ตรวจสอบ OS: ถ้าเป็น Linux (Pi) ให้ใช้ GStreamer Pipeline
        # ถ้าเป็น Windows/Mac ให้ใช้ index 0 ปกติ
        if platform.system() == 'Linux':
            # Pipeline สำหรับ Pi 5 ที่ลื่นไหล
            gst_str = (
                "libcamerasrc ! "
                "video/x-raw, width=640, height=480, framerate=30/1 ! "
                "videoconvert ! "
                "appsink"
            )
            self.capture = cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
        else:
            self.capture = cv2.VideoCapture(0)

        # ตั้งเวลาอัปเดตภาพ (30 FPS)
        Clock.schedule_interval(self.update, 1.0 / 30.0)
        return self.img1

    def update(self, dt):
        ret, frame = self.capture.read()
        if ret:
            # 1. พลิกภาพให้หัวตั้ง (OpenCV บางทีกลับหัว)
            frame = cv2.flip(frame, 0) 

            # 2. แปลงจาก BGR (OpenCV) เป็น Texture (Kivy)
            # วิธีนี้เร็วและไม่ Block UI
            buf = cv2.flip(frame, 0).tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            
            # 3. ส่งเข้าหน้าจอ
            self.img1.texture = texture

    def on_stop(self):
        self.capture.release()

if __name__ == '__main__':
    CamApp().run()