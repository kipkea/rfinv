import os
import requests
import threading
from datetime import datetime

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.lang import Builder
from kivy.core.window import Window

# กำหนด URL ของ API (เปลี่ยน localhost เป็น IP ของเครื่อง Server หากรันคนละเครื่อง)
API_BASE_URL = "http://127.0.0.1:8000/api"

# --- KV Design สำหรับหน้าจอนี้ ---
Builder.load_string('''
<RegisterItemScreen>:
    name: 'register_screen'
    BoxLayout:
        orientation: 'vertical'
        padding: 10
        spacing: 10
        
        # --- ส่วนหัว: เลือกประเภท ---
        Label:
            text: "ลงทะเบียนรายการใหม่ (Registration)"
            font_size: '20sp'
            size_hint_y: None
            height: 40
            
        BoxLayout:
            size_hint_y: None
            height: 50
            spacing: 10
            ToggleButton:
                id: btn_type_inv
                text: "สินค้า (Inventory)"
                group: "item_type"
                state: 'down' # ค่าเริ่มต้น
                background_color: (0, 0.7, 0.9, 1) if self.state == 'down' else (0.5, 0.5, 0.5, 1)
            ToggleButton:
                id: btn_type_loc
                text: "สถานที่ (Location)"
                group: "item_type"
                background_color: (0, 0.9, 0, 1) if self.state == 'down' else (0.5, 0.5, 0.5, 1)

        # --- ส่วนกรอกข้อมูล RFID ---
        BoxLayout:
            size_hint_y: None
            height: 50
            spacing: 10
            TextInput:
                id: input_rfid
                hint_text: "RFID Code (กดปุ่ม Scan หรือพิมพ์)"
                multiline: False
                readonly: False # ให้พิมพ์แก้ได้ถ้าต้องการ
            Button:
                text: "SCAN RFID"
                size_hint_x: 0.3
                background_color: (1, 0.5, 0, 1)
                on_release: root.simulate_rfid_scan()

        # --- ส่วนกรอกรายละเอียด ---
        TextInput:
            id: input_name
            hint_text: "ชื่อรายการ (Name)"
            size_hint_y: None
            height: 40
            multiline: False

        TextInput:
            id: input_detail
            hint_text: "รายละเอียดเพิ่มเติม (Description)"
            size_hint_y: 0.2

        # --- ส่วนกล้องถ่ายรูป ---
        BoxLayout:
            orientation: 'vertical'
            Label:
                text: "รูปภาพสินค้า:"
                size_hint_y: None
                height: 30
            
            # ใช้ Camera Widget ของ Kivy (index 0 คือกล้องตัวแรก)
            # หมายเหตุ: ถ้าบน PC ไม่มีกล้อง อาจต้องเปลี่ยนเป็น Image ธรรมดา
            Camera:
                id: camera_preview
                resolution: (640, 480)
                play: True
                allow_stretch: True
            
            Button:
                text: "จับภาพ (Capture)"
                size_hint_y: None
                height: 40
                on_release: root.capture_photo()

        # --- ปุ่มบันทึก ---
        Button:
            text: "บันทึกข้อมูล (SAVE)"
            size_hint_y: None
            height: 60
            background_color: (0, 0.8, 0, 1)
            on_release: root.save_data_process()
            
        # --- Status Label ---
        Label:
            id: lbl_status
            text: "Ready"
            size_hint_y: None
            height: 30
            color: (1, 1, 0, 1)
''')

class RegisterItemScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image_path = None # ตัวแปรเก็บ path รูปภาพชั่วคราว

    def simulate_rfid_scan(self):
        """
        จำลองการอ่านค่า RFID (ในเครื่องจริง ให้เรียก Driver ของ Reader ตรงนี้)
        """
        import random
        # สุ่มเลข Hex 24 ตัว (มาตรฐาน EPC Gen 2)
        mock_rfid = "E200" + "".join([random.choice('0123456789ABCDEF') for _ in range(20)])
        self.ids.input_rfid.text = mock_rfid
        self.ids.lbl_status.text = f"Scanned: {mock_rfid}"

    def capture_photo(self):
        """
        จับภาพจาก Camera Widget และบันทึกลงไฟล์ชั่วคราว
        """
        camera = self.ids.camera_preview
        if not camera:
            self.ids.lbl_status.text = "Camera not found!"
            return

        # สร้างชื่อไฟล์ตามเวลา
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"capture_{timestamp}.png"
        
        # บันทึกภาพ
        camera.export_to_png(filename)
        self.image_path = filename # เก็บ path ไว้ส่ง API
        
        self.ids.lbl_status.text = f"Photo saved: {filename}"
        # หยุดกล้องชั่วคราวเพื่อโชว์ภาพนิ่ง (Optional)
        # camera.play = False 

    def save_data_process(self):
        """
        เริ่ม Thread การบันทึก (เพื่อไม่ให้หน้าจอค้าง)
        """
        t = threading.Thread(target=self._save_to_api)
        t.start()

    def _save_to_api(self):
        # 1. เตรียมข้อมูล
        rfid_code = self.ids.input_rfid.text.strip()
        name = self.ids.input_name.text.strip()
        detail = self.ids.input_detail.text.strip()
        is_inventory = self.ids.btn_type_inv.state == 'down'

        if not rfid_code or not name:
            self.update_status("Error: กรุณาใส่ RFID และชื่อ")
            return

        try:
            # 2. สร้าง/ตรวจสอบ RFID Tag ก่อน (POST /api/tags/)
            # หมายเหตุ: API ที่เราทำไว้อาจจะต้องการให้มี Tag ในระบบก่อน
            tag_data = {
                "rfid_code": rfid_code,
                "is_location": not is_inventory
            }
            # ลองสร้าง Tag (ถ้าซ้ำ API อาจจะ Error 400 หรือ 200 แล้วแต่ Django logic)
            # ในที่นี้สมมติว่าถ้าซ้ำก็ไม่เป็นไร เราจะเอา ID มันมาใช้
            tag_response = requests.post(f"{API_BASE_URL}/tags/", json=tag_data)
            
            # ถ้าสร้างไม่ได้ หรือมีอยู่แล้ว ต้องดึง ID ของ Tag นั้นมา
            tag_id = None
            if tag_response.status_code == 201:
                tag_id = tag_response.json().get('id')
            else:
                # กรณีมีอยู่แล้ว ให้ลอง GET หา ID
                get_tag = requests.get(f"{API_BASE_URL}/tags/?search={rfid_code}")
                if get_tag.status_code == 200 and len(get_tag.json()) > 0:
                    tag_id = get_tag.json()[0]['id']
            
            if not tag_id:
                self.update_status("Error: ไม่สามารถจัดการ RFID Tag ได้")
                return

            # 3. บันทึกข้อมูล Location หรือ Inventory
            files = {}
            if self.image_path and os.path.exists(self.image_path):
                # เปิดไฟล์รูปภาพเพื่อเตรียมส่ง
                files = {'image': open(self.image_path, 'rb')}

            if is_inventory:
                # --- กรณีสินค้า (Inventory) ---
                payload = {
                    "name": name,
                    "detail": detail,
                    "rfid_tag": tag_id, # ส่ง ID ของ Tag
                    # "current_location": 1 # (Optional) ถ้าต้องการระบุ location เริ่มต้น
                }
                # ใช้ multipart/form-data อัตโนมัติเมื่อมี files
                response = requests.post(f"{API_BASE_URL}/inventory/", data=payload, files=files)
            
            else:
                # --- กรณีสถานที่ (Location) ---
                payload = {
                    "name": name,
                    "description": detail,
                    "rfid_tag": tag_id
                }
                # Location Model ของเราอาจจะไม่มีรูปภาพ ก็ไม่ต้องส่ง files
                response = requests.post(f"{API_BASE_URL}/locations/", data=payload)

            # 4. ปิดไฟล์รูปภาพ (ถ้าเปิดไว้)
            if 'image' in files:
                files['image'].close()
                # os.remove(self.image_path) # ลบไฟล์ชั่วคราวทิ้งก็ได้

            # 5. ตรวจสอบผลลัพธ์
            if response.status_code in [200, 201]:
                self.update_status("Success: บันทึกข้อมูลเรียบร้อย!")
                # ล้างหน้าจอ
                self.clear_form()
            else:
                self.update_status(f"API Error: {response.text}")

        except Exception as e:
            self.update_status(f"Connection Error: {str(e)}")

    def update_status(self, text):
        """อัปเดตข้อความบน UI (ต้องทำผ่าน main thread ถ้าใช้ Kivy Clock แต่นี่แบบง่าย)"""
        self.ids.lbl_status.text = text

    def clear_form(self):
        """ล้างช่องกรอกข้อมูล"""
        self.ids.input_rfid.text = ""
        self.ids.input_name.text = ""
        self.ids.input_detail.text = ""
        self.ids.camera_preview.play = True
        self.image_path = None