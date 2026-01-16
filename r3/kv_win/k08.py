from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from camera4kivy import Preview
import time

# KV Layout: กำหนดหน้าตา UI
kv = """
BoxLayout:
    orientation: 'vertical'
    
    # ส่วนแสดงผลกล้อง (Preview)
    Preview:
        id: camera_preview
        camera_id: "0"  # ลองระบุ ID ตรงๆ (บางทีอาจเป็น "libcamerasrc")
        aspect_ratio: '16:9'
        letterbox_color: 0, 0, 0, 1

    # ปุ่มควบคุม
    Button:
        text: 'Capture / Analyze'
        size_hint_y: None
        height: '48dp'
        on_press: app.capture_action()
"""

class CameraApp(App):
    def build(self):
        return Builder.load_string(kv)

    def on_start(self):
        # เริ่มต้นการทำงานกล้องเมื่อแอปเปิด
        # บน Pi 5 มันจะหา libcamera โดยอัตโนมัติผ่าน GStreamer
        self.root.ids.camera_preview.connect_camera(enable_analyze_pixels=True)

    def on_stop(self):
        # ปิดกล้องเมื่อปิดแอป
        self.root.ids.camera_preview.disconnect_camera()

    def capture_action(self):
        print("Capture button pressed!")
        # ตัวอย่าง: การดึงภาพมาใช้ (ถ้าต้องการ save หรือส่งไป opencv)
        # camera4kivy มี method capture_screenshot() หรือใช้ analyze api
        self.root.ids.camera_preview.capture_screenshot()

if __name__ == '__main__':
    CameraApp().run()