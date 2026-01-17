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
from kivy.uix.widget import Widget
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

from dotenv import load_dotenv
import telepot
from telepot.loop import MessageLoop

#####################################
# โหลดค่า environment จากไฟล์ .env
load_dotenv()

APISERVER = os.getenv("APISERVER")
key = os.getenv("key")

#telegram 
bot_token = os.getenv("bot_token")
bot_id = os.getenv("bot_id")
######################################

clear = lambda: os.system('clear')

#Builder.load_string(KV_CODE)
Builder.load_file('rfinv.kv')

class AppTabs(TabbedPanel):
    # --- Camera Properties ---
    capture = ObjectProperty(None, allownone=True)
    camera_update_event = ObjectProperty(None, allownone=True)
    available_cameras = ListProperty([])
    captured_frame = ObjectProperty(None, allownone=True)
    active_camera_index = NumericProperty(-1)
    sort_reverse = False
    
    # API URLs
    API_URL = 'http://localhost:8000/api/basic/'
    API_GALLERY_URL = 'http://localhost:8000/api/gallery/'
    API_UPLOAD_URL = 'http://localhost:8000/api/upload/'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(current_tab=self.on_tab_switch)
        threading.Thread(target=self.detect_cameras, daemon=True).start()

    # --- Helper Function for Status Bar ---
    def set_global_status(self, text, zone='center'):
        """
        ส่งข้อความไปยัง MainLayout เพื่อแสดงที่ Status Bar
        zone: 'left', 'center', 'right'
        """
        if self.parent and hasattr(self.parent, 'update_footer'):
            self.parent.update_footer(text, zone)

    def on_tab_switch(self, instance, value):
        tab_text = value.text
        self.set_global_status(f"Switched to tab: {tab_text}", 'center')

        if tab_text == 'Camera':
            self.start_camera_preview()
        else:
            self.stop_camera_preview()

        if tab_text == 'Gallery':
            self.fetch_gallery()

    def show_exit_popup(self):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_label = Label(text='Are you sure you want to exit?')
        buttons_layout = BoxLayout(size_hint_y=None, height='50dp', spacing=10)
        yes_button = Button(text='Yes')
        no_button = Button(text='No')
        buttons_layout.add_widget(yes_button)
        buttons_layout.add_widget(no_button)
        content.add_widget(popup_label)
        content.add_widget(buttons_layout)
        popup = Popup(title='Confirm Exit', content=content, size_hint=(None, None), size=(400, 200), auto_dismiss=False)
        yes_button.bind(on_press=lambda *args: App.get_running_app().stop())
        no_button.bind(on_press=popup.dismiss)
        popup.open()

    # --- Command Runner ---
    def run_command(self):
        command = self.ids.cmd_input.text
        if not command: return
        self.set_global_status(f"Running: {command}...", 'center')
        threading.Thread(target=self._execute_command, args=(command,), daemon=True).start()

    def _execute_command(self, command):
        try:
            process = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            result = process.stdout if process.returncode == 0 else process.stderr
            status = "Command Success" if process.returncode == 0 else "Command Failed"
        except Exception as e:
            result = str(e)
            status = "Command Error"
        
        self._update_cmd_output(result)
        # Update status in main thread
        Clock.schedule_once(lambda dt: self.set_global_status(status, 'center'))

    @mainthread
    def _update_cmd_output(self, text):
        self.ids.output_text.text = text

    # --- Camera Functions ---
    @mainthread
    def update_camera_spinner(self):
        self.ids.camera_spinner.values = [f"Cam {i}" for i in self.available_cameras]
        if self.available_cameras:
            self.ids.camera_spinner.text = f"Cam {self.available_cameras[0]}"
            self.active_camera_index = self.available_cameras[0]
            self.set_global_status(f"Camera {self.active_camera_index} Connected", 'left')
        else:
            self.set_global_status("No cameras found", 'left')

    def detect_cameras(self):
        self.set_global_status("Detecting cameras...", 'left')
        found_indices = set()
        for i in range(5): # Reduced range for speed
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    found_indices.add(i)
                cap.release()
            
            if i not in found_indices:
                cap = cv2.VideoCapture(i, cv2.CAP_ANY)
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        found_indices.add(i)
                    cap.release()
        
        self.available_cameras = sorted(list(found_indices))
        self.update_camera_spinner()

    def start_camera_preview(self):
        if self.active_camera_index == -1: return
        self.capture = cv2.VideoCapture(self.active_camera_index)
        if self.camera_update_event: self.camera_update_event.cancel()
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
                self.set_global_status(f"Switched to Cam {new_index}", 'left')
        except (ValueError, IndexError):
            pass

    def update_camera_view(self, dt):
        if self.capture:
            ret, frame = self.capture.read()
            if ret:
                buf = cv2.flip(frame, 0).tobytes()
                texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
                texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
                self.ids.camera_view.texture = texture

    def capture_image(self):
        if self.capture:
            ret, frame = self.capture.read()
            if ret:
                self.captured_frame = frame
                buf = cv2.flip(frame, 0).tobytes()
                texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
                texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
                self.ids.capture_preview.texture = texture
                self.ids.save_btn.disabled = False
                self.ids.camera_local_status.text = "Captured!"
                self.set_global_status("Image Captured. Waiting to save...", 'center')

    def save_image_api(self):
        if self.captured_frame is None: return
        self.ids.save_btn.disabled = True
        self.set_global_status("Uploading image...", 'center')
        
        is_success, buffer = cv2.imencode(".jpg", self.captured_frame)
        if not is_success:
            self.set_global_status("Encoding Failed", 'center')
            return

        filename = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        payload = {'user': 'kivy_app_user'}
        files = {'image_file': (filename, buffer.tobytes(), 'image/jpeg')}
        threading.Thread(target=self._upload_request, args=(payload, files), daemon=True).start()

    def _upload_request(self, payload, files):
        try:
            response = requests.post(self.API_UPLOAD_URL, data=payload, files=files, timeout=15)
            if response.status_code == 201:
                Clock.schedule_once(lambda dt: self.set_global_status("Upload Successful!", 'center'))
            else:
                Clock.schedule_once(lambda dt: self.set_global_status(f"Upload Error: {response.status_code}", 'center'))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.set_global_status(f"Connection Failed", 'center'))

    # --- Product API ---
    def fetch_data(self):
        self.set_global_status("Fetching Products...", 'center')
        # Simulate API call for demo purposes
        self.simulate_api_call()

    def on_api_success(self, req, result):
        data_list = []
        for i, item in enumerate(result, 1):
            data_list.append({
                'index': str(i),
                'code': item.get('code', ''),
                'desc': item.get('desc', ''),
                'location': item.get('location', ''),
                'date': item.get('date', ''),
                'img_url': item.get('image_url', '')
            })
        self.ids.rv_products.data = data_list
        self.set_global_status(f"Loaded {len(data_list)} items", 'center')

    def sort_data(self, key):
        data = self.ids.rv_products.data
        self.sort_reverse = not self.sort_reverse
        try:
            sorted_data = sorted(data, key=lambda x: x[key], reverse=self.sort_reverse)
            self.ids.rv_products.data = sorted_data
            self.set_global_status(f"Sorted by {key}", 'center')
        except KeyError:
            pass

    def simulate_api_call(self):
        # Mock data
        Clock.schedule_once(lambda dt: self._process_mock_data(), 0.5)

    def _process_mock_data(self):
        mock_data = [
            {'code': 'A001', 'desc': 'ปากกา', 'location': 'Shelf 1', 'date': '2023-10-01', 'image_url': 'https://cdmc.coj.go.th/cms/u1/20180611f9829f3a4145d4678f38a76d.png'},
            {'code': 'B002', 'desc': 'สมุดโน้ต', 'location': 'Shelf 2', 'date': '2023-09-15', 'image_url': 'https://cdmc.coj.go.th/cms/u1/20180611f9829f3a4145d4678f38a76d.png'},
            {'code': 'A003', 'desc': 'ดินสอ', 'location': 'Shelf 1', 'date': '2023-10-05', 'image_url': 'https://cdmc.coj.go.th/cms/u1/20180611f9829f3a4145d4678f38a76d.png'},
        ]
        self.on_api_success(None, mock_data)

    # --- Gallery API ---
    def fetch_gallery(self):
        self.set_global_status("Fetching Gallery...", 'center')
        UrlRequest(self.API_GALLERY_URL, on_success=self.on_gallery_success, on_failure=self.on_gallery_error, on_error=self.on_gallery_error)

    def on_gallery_success(self, req, result):
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
        self.set_global_status(f"Gallery Loaded ({len(data_list)})", 'center')

    def on_gallery_error(self, req, error):
        self.set_global_status("Gallery Load Failed", 'center')

# --- MainLayout ใหม่ที่เป็น Root Widget (แนวตั้ง) ---
class MainLayout(BoxLayout):
    @mainthread
    def update_footer(self, text, zone='center'):
        """
        อัปเดตข้อความใน Footer
        zone: 'left', 'center', 'right'
        """
        if zone == 'left':
            self.ids.status_left.text = text
        elif zone == 'right':
            self.ids.status_right.text = text
        else:
            self.ids.status_center.text = text

class KivyApp(App):
    def build(self):
        Window.bind(on_request_close=self.on_request_close)        
        return MainLayout()

    def on_request_close(self, *args):
        # เข้าถึง AppTabs ผ่าน ids ของ MainLayout
        self.root.ids.app_tabs.show_exit_popup()
        return True

if __name__ == '__main__':
    if not os.path.exists('placeholder.png'):
        cv2.imwrite('placeholder.png', np.zeros((100, 100, 3), dtype=np.uint8))
    KivyApp().run()
    cv2.destroyAllWindows()
    
    