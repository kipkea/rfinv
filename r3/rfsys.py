import json
from kivy.app import App
from kivy.lang import Builder
import cv2
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.network.urlrequest import UrlRequest
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import StringProperty, ObjectProperty, ListProperty, NumericProperty
from kivy.uix.popup import Popup
from kivy.clock import mainthread, Clock
from kivy.graphics.texture import Texture
import requests
import subprocess
import threading
import numpy as np
import os
from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image

###Screen Layout and Logic###
from kivy.uix.screenmanager import ScreenManager
from Screen.RegisterItemScreen import RegisterItemScreen

# --- ส่วน KV Language ---
Builder.load_file('kv/rfsys.kv')

class MainLayout(TabbedPanel):
    '''
    # --- Camera Properties ---
    capture = ObjectProperty(None, allownone=True)
    camera_update_event = ObjectProperty(None, allownone=True)
    available_cameras = ListProperty([])
    captured_frame = ObjectProperty(None, allownone=True)
    active_camera_index = NumericProperty(-1)
    '''

    # เก็บสถานะการเรียงลำดับ (Ascending/Descending)
    sort_reverse = False
    
    # URL ของ Django API (ตัวอย่าง)
    #API_URL = 'http://127.0.0.1:8000/api/products/' 
    API_URL = 'http://localhost:8000/api/basic/'
    API_GALLERY_URL = 'http://localhost:8000/api/gallery/'
    API_UPLOAD_URL = 'http://localhost:8000/api/upload/'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ผูกฟังก์ชันกับการเปลี่ยนแท็บ
        self.bind(current_tab=self.on_tab_switch)
        # ตรวจจับกล้องเมื่อเริ่มต้น
        threading.Thread(target=self.detect_cameras, daemon=True).start()

    def on_tab_switch(self, instance, value):
        """ถูกเรียกเมื่อมีการสลับแท็บ"""
        # `value` คือ TabbedPanelItem ที่ถูกเลือก
        tab_text = value.text

        if tab_text == 'Camera':
            self.start_camera_preview()
        else: # หยุดกล้องเมื่อออกจากแท็บ Camera
            self.stop_camera_preview()

        if tab_text == 'Gallery':
            self.fetch_gallery()

    def show_exit_popup(self):
        """แสดง Popup ยืนยันการออกจากโปรแกรม"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_label = Label(text='Are you sure you want to exit?')
        
        buttons_layout = BoxLayout(size_hint_y=None, height='50dp', spacing=10)
        yes_button = Button(text='Yes')
        no_button = Button(text='No')
        buttons_layout.add_widget(yes_button)
        buttons_layout.add_widget(no_button)

        content.add_widget(popup_label)
        content.add_widget(buttons_layout)

        popup = Popup(title='Confirm Exit',
                      content=content,
                      size_hint=(None, None), size=(400, 200),
                      auto_dismiss=False)

        # กำหนดการทำงานของปุ่ม
        yes_button.bind(on_press=lambda *args: App.get_running_app().stop())
        no_button.bind(on_press=popup.dismiss)

        popup.open()


    def run_command(self):
        """ฟังก์ชันสำหรับ Tab 1 (Command Runner)"""
        command = self.ids.cmd_input.text
        if not command: return
        threading.Thread(target=self._execute_command, args=(command,), daemon=True).start()

    def _execute_command(self, command):
        try:
            process = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            result = process.stdout if process.returncode == 0 else process.stderr
        except Exception as e:
            result = str(e)
        self._update_cmd_output(result)

    @mainthread
    def _update_cmd_output(self, text):
        self.ids.output_text.text = text

    # --- ฟังก์ชันสำหรับ Tab 3 (Camera) ---
    '''
    @mainthread
    def update_camera_spinner(self):
        self.ids.camera_spinner.values = [f"Cam {i}" for i in self.available_cameras]
        if self.available_cameras:
            self.ids.camera_spinner.text = f"Cam {self.available_cameras[0]}"
            self.active_camera_index = self.available_cameras[0]
            self.ids.camera_status_label.text = f"Using Camera Index: {self.active_camera_index}"
        else:
            self.ids.camera_status_label.text = "No cameras found."

    def detect_cameras(self):
        """ตรวจหากล้องที่เชื่อมต่ออยู่ (ทำงานใน Thread)"""
        found_indices = set()
        
        # ตรวจสอบกล้องโดยลองใช้ API หลายแบบเพื่อให้ครอบคลุมมากขึ้น
        for i in range(5): # ตรวจสอบ 5 index แรก
            # วิธีที่ 1: ลองใช้ DirectShow (CAP_DSHOW) ก่อน ซึ่งมักจะเข้ากันได้ดีกับกล้อง USB บน Windows
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    found_indices.add(i)
                    cap.release()
                    continue # เมื่อเจอแล้ว ให้ข้ามไปเช็ค index ถัดไปเลย
                cap.release()

            # วิธีที่ 2: หากวิธีแรกไม่สำเร็จ ลองใช้ API เริ่มต้น (CAP_ANY)
            cap = cv2.VideoCapture(i, cv2.CAP_ANY)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    found_indices.add(i)
                cap.release()
        
        self.available_cameras = sorted(list(found_indices))
        self.update_camera_spinner()

    def start_camera_preview(self):
        if self.active_camera_index == -1:
            return
        self.capture = cv2.VideoCapture(self.active_camera_index)
        if self.camera_update_event:
            self.camera_update_event.cancel()
        self.camera_update_event = Clock.schedule_interval(self.update_camera_view, 1.0 / 30.0)

    def stop_camera_preview(self):
        if self.camera_update_event:
            self.camera_update_event.cancel()
            self.camera_update_event = None
        if self.capture:
            self.capture.release()
            self.capture = None

    def switch_camera(self, text):
        try:
            new_index = int(text.split(' ')[1])
            if new_index != self.active_camera_index:
                self.active_camera_index = new_index
                self.stop_camera_preview()
                self.start_camera_preview()
                self.ids.camera_status_label.text = f"Switched to Camera Index: {self.active_camera_index}"
        except (ValueError, IndexError):
            pass

    def update_camera_view(self, dt):
        if self.capture:
            ret, frame = self.capture.read()
            if ret:
                # แปลง frame BGR ของ OpenCV เป็น Texture ของ Kivy
                buf = cv2.flip(frame, 0).tobytes()
                texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
                texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
                self.ids.camera_view.texture = texture

    def capture_image(self):
        if self.capture:
            ret, frame = self.capture.read()
            if ret:
                self.captured_frame = frame
                # แสดงภาพตัวอย่าง
                buf = cv2.flip(frame, 0).tobytes()
                texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
                texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
                self.ids.capture_preview.texture = texture
                self.ids.save_btn.disabled = False
                self.ids.camera_status_label.text = "Image captured. Ready to save."

    def save_image_api(self):
        if self.captured_frame is None:
            return
        self.ids.save_btn.disabled = True
        self.ids.camera_status_label.text = "Uploading..."

        # แปลง frame เป็น bytes สำหรับส่ง
        is_success, buffer = cv2.imencode(".jpg", self.captured_frame)
        if not is_success:
            self.ids.camera_status_label.text = "Failed to encode image."
            return

        # สร้างชื่อไฟล์
        filename = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        
        # ข้อมูลที่จะส่ง (เช่น user)
        payload = {'user': 'kivy_app_user'}
        files = {'image_file': (filename, buffer.tobytes(), 'image/jpeg')}

        # ใช้ requests ใน Thread เพื่อไม่ให้ UI ค้าง
        threading.Thread(target=self._upload_request, args=(payload, files), daemon=True).start()

    def _upload_request(self, payload, files):
        try:
            response = requests.post(self.API_UPLOAD_URL, data=payload, files=files, timeout=15)
            if response.status_code == 201:
                self.update_camera_status("Upload successful!")
            else:
                self.update_camera_status(f"Error: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            self.update_camera_status(f"Upload failed: {e}")

    @mainthread
    def update_camera_status(self, message):
        self.ids.camera_status_label.text = message
        self.ids.save_btn.disabled = self.captured_frame is None
    '''

    # --- ฟังก์ชันสำหรับ Tab 2 (Product API) ---

    def fetch_data(self):
        """เรียกข้อมูลจาก API ด้วย UrlRequest"""
        # หมายเหตุ: ในการใช้งานจริง เปลี่ยน API_URL เป็น URL ของคุณ
        # หากไม่มี Server จริง สามารถจำลองข้อมูลได้โดยข้ามไปเรียก self.on_api_success(req, mock_data)
        
        print(f"Fetching from {self.API_URL}...")
        
        # ใช้ UrlRequest เพื่อไม่ให้หน้าจอค้างขณะรอข้อมูล
        #UrlRequest(self.API_URL, on_success=self.on_api_success, on_failure=self.on_api_error, on_error=self.on_api_error)

        # *สำหรับการทดสอบหากไม่มี Server* ให้คอมเมนต์บรรทัดบนและใช้บรรทัดล่างนี้แทน:
        self.simulate_api_call()

    def on_api_success(self, req, result):
        """ทำงานเมื่อได้รับ JSON กลับมาสำเร็จ"""
        # สมมติว่า JSON ที่ได้เป็น List ของ Dict เช่น:
        # [{"id": 1, "code": "P001", "desc": "สินค้า A", "loc": "A1", "date": "2023-10-01", "img": "http..."}, ...]
        
        data_list = []
        for i, item in enumerate(result, 1):
            data_list.append({
                'index': str(i),
                'code': item.get('code', ''),
                'desc': item.get('desc', ''),
                'location': item.get('location', ''),
                'date': item.get('date', ''),
                'img_url': item.get('image_url', '') # URL รูปภาพ
            })
        
        # อัปเดตข้อมูลเข้า RecycleView
        self.ids.rv_products.data = data_list
        print("Data loaded successfully.")

    def on_api_error(self, req, error):
        print(f"API Error: {error}")
        # กรณี Error อาจแสดง Popup แจ้งเตือน

    def sort_data(self, key):
        """ฟังก์ชันเรียงลำดับข้อมูลเมื่อคลิกหัวตาราง"""
        data = self.ids.rv_products.data
        
        # สลับลำดับการเรียง (มากไปน้อย <-> น้อยไปมาก)
        self.sort_reverse = not self.sort_reverse
        
        # เรียงข้อมูลโดยใช้ Key ที่ส่งมา
        # ใช้ lambda เพื่อดึงค่าจาก dict ตาม key ที่ระบุ
        try:
            sorted_data = sorted(
                data, 
                key=lambda x: x[key], 
                reverse=self.sort_reverse
            )
            self.ids.rv_products.data = sorted_data
        except KeyError:
            print(f"Key {key} not found in data")

    def simulate_api_call(self):
        """ข้อมูลจำลองสำหรับทดสอบ (Mock Data)"""
        mock_data = [
            {'code': 'A001', 'desc': 'ปากกา', 'location': 'Shelf 1', 'date': '2023-10-01', 'image_url': 'https://cdmc.coj.go.th/cms/u1/20180611f9829f3a4145d4678f38a76d.png'},
            {'code': 'B002', 'desc': 'สมุดโน้ต', 'location': 'Shelf 2', 'date': '2023-09-15', 'image_url': 'https://cdmc.coj.go.th/cms/u1/20180611f9829f3a4145d4678f38a76d.png'},
            {'code': 'A003', 'desc': 'ดินสอ', 'location': 'Shelf 1', 'date': '2023-10-05', 'image_url': 'https://cdmc.coj.go.th/cms/u1/20180611f9829f3a4145d4678f38a76d.png'},
            {'code': 'C001', 'desc': 'ยางลบ', 'location': 'Shelf 3', 'date': '2023-08-20', 'image_url': 'https://cdmc.coj.go.th/cms/u1/20180611f9829f3a4145d4678f38a76d.png'},
        ]
        self.on_api_success(None, mock_data)

    # --- ฟังก์ชันสำหรับ Tab 4 (Gallery) ---

    def fetch_gallery(self):
        """ดึงข้อมูลรูปภาพจาก API"""
        UrlRequest(self.API_GALLERY_URL, on_success=self.on_gallery_success, on_failure=self.on_gallery_error, on_error=self.on_gallery_error)

    def on_gallery_success(self, req, result):
        """ทำงานเมื่อได้รับข้อมูลแกลเลอรีสำเร็จ"""
        # result คาดว่าเป็น list of dicts
        # [{"filename": "img.jpg", "timestamp": "...", "user": "...", "dimensions": "WxH", "image_url": "http..."}, ...]
        data_list = []
        for item in result:
            data_list.append({
                'filename': item.get('filename', 'N/A'),
                'timestamp': item.get('timestamp', 'N/A'),
                'user': item.get('user', 'N/A'),
                'dimensions': item.get('dimensions', 'N/A'),
                'image_url': item.get('image_url', '')
            })
        self.ids.rv_gallery.data = sorted(data_list, key=lambda x: x['timestamp'], reverse=True)

    def on_gallery_error(self, req, error):
        print(f"Gallery API Error: {error}")

class KivyApp(App):
    def build(self):
        Window.bind(on_request_close=self.on_request_close)
        return MainLayout()

    def on_request_close(self, *args):
        """
        ถูกเรียกเมื่อผู้ใช้พยายามจะปิดหน้าต่าง (เช่น กดปุ่มกากบาท)
        เราจะแสดง popup ยืนยันแทนการปิดทันที
        """
        self.root.show_exit_popup()
        return True # คืนค่า True เพื่อบอก Kivy ว่าเราจัดการ event นี้แล้ว และไม่ต้องปิดหน้าต่าง


if __name__ == '__main__':
    # สร้าง placeholder image เผื่อไม่มี
    if not os.path.exists('placeholder.png'):
        cv2.imwrite('placeholder.png', np.zeros((100, 100, 3), dtype=np.uint8))
    KivyApp().run()