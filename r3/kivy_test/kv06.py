# main.py
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, StringProperty
from kivy.metrics import dp
from kivy.lang import Builder # ยังคงใช้ Builder เพื่อโหลดไฟล์ .kv
from kivy.core.window import Window
from kivy.config import Config # Import Config ที่นี่เลย

import json # สำหรับจัดการ keyboard layout
import os # สำหรับจัดการไฟล์/โฟลเดอร์

# ไม่ได้ติดตั้งบนเครื่องนี้
# from picamera import PiCamera # สำหรับ Raspberry Pi camera
# import serial # สำหรับ RFID reader (USB serial)
# import cv2 # สำหรับกล้องอื่นๆ หรือประมวลผลภาพ

# --- Screen Classes ---
# คลาสเหล่านี้จะถูกเชื่อมโยงกับ UI ที่อยู่ใน inventory.kv โดยอัตโนมัติ
# ตราบใดที่ชื่อคลาสใน Python ตรงกับชื่อใน .kv (เช่น <MenuScreen>: -> class MenuScreen(Screen):)

class MenuScreen(Screen):
    pass

class ScanRFIDScreen(Screen):
    def on_enter(self):
        # เคลียร์ค่าเมื่อเข้ามาหน้านี้ใหม่
        self.ids.rfid_input.text = ''
        self.ids.status_label.text = 'รอการสแกน...'
        self.ids.product_info_label.text = ''
        self.ids.product_image.source = ''

    def start_rfid_scan(self):
        self.ids.status_label.text = 'กำลังรอ RFID tag...'
        # --- โค้ดเชื่อมต่อ RFID Reader จริงๆ จะอยู่ตรงนี้ ---
        # ตัวอย่าง: อ่านค่าจาก Serial Port (สมมติว่า RFID reader ต่อผ่าน USB/UART)
        # try:
        #     ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1) # แก้ไข port และ baudrate ตามจริง
        #     rfid_tag = ser.readline().decode('utf-8').strip()
        #     if rfid_tag:
        #         self.ids.rfid_input.text = rfid_tag
        #         self.search_product()
        #     else:
        #         self.ids.status_label.text = 'ไม่พบ RFID tag'
        #     ser.close()
        # except Exception as e:
        #     self.ids.status_label.text = f'RFID Error: {e}'
        # ----------------------------------------------------

        # ตัวอย่างจำลอง: หากไม่มี RFID reader จริง ให้กดปุ่มเพื่อจำลองค่า
        from kivy.clock import Clock
        Clock.schedule_once(self._simulate_rfid_read, 2) # จำลองการอ่านหลังจาก 2 วินาที

    def _simulate_rfid_read(self, dt):
        simulated_tag = "RFID12345" # หรือ "RFID67890" เพื่อลองอีกเคส
        self.ids.rfid_input.text = simulated_tag
        self.ids.status_label.text = f'พบ RFID Tag: {simulated_tag}'
        self.search_product()

    def search_product(self):
        rfid_tag = self.ids.rfid_input.text
        if not rfid_tag:
            self.ids.status_label.text = 'กรุณาใส่ RFID Tag'
            return

        self.ids.status_label.text = f'กำลังค้นหาสินค้าสำหรับ {rfid_tag}...'
        # --- โค้ดเรียก Django API เพื่อดึงข้อมูลสินค้า ---
        # import requests
        # try:
        #     # สมมติว่า Django API อยู่ที่ http://your-aws-api.com/api/products/{rfid_tag}/
        #     response = requests.get(f'http://your-aws-api.com/api/products/{rfid_tag}/')
        #     if response.status_code == 200:
        #         product_data = response.json()
        #         self.ids.product_info_label.text = (
        #             f"ชื่อสินค้า: {product_data.get('name', 'N/A')}\n"
        #             f"จำนวน: {product_data.get('quantity', 'N/A')}\n"
        #             f"รายละเอียด: {product_data.get('description', 'N/A')}"
        #         )
        #         image_url = product_data.get('image', '')
        #         if image_url:
        #             self.ids.product_image.source = image_url
        #         else:
        #             self.ids.product_image.source = '' # ไม่มีรูป
        #         self.ids.status_label.text = 'พบข้อมูลสินค้า'
        #     elif response.status_code == 404:
        #         self.ids.product_info_label.text = 'ไม่พบสินค้าสำหรับ RFID Tag นี้'
        #         self.ids.product_image.source = ''
        #         self.ids.status_label.text = 'ไม่พบข้อมูล'
        #     else:
        #         self.ids.product_info_label.text = f'ข้อผิดพลาด API: {response.status_code}'
        #         self.ids.product_image.source = ''
        #         self.ids.status_label.text = 'ข้อผิดพลาด'
        # except requests.exceptions.RequestException as e:
        #     self.ids.product_info_label.text = f'เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}'
        #     self.ids.product_image.source = ''
        #     self.ids.status_label.text = 'ข้อผิดพลาดการเชื่อมต่อ'
        # ------------------------------------------------------------------

        # ตัวอย่างข้อมูลจำลอง (เพื่อการทดสอบโดยไม่ต้องเชื่อมต่อ API จริง)
        if rfid_tag == "RFID12345":
            self.ids.product_info_label.text = (
                "ชื่อสินค้า: Raspberry Pi 4 Model B\n"
                "จำนวน: 10\n"
                "รายละเอียด: บอร์ดคอมพิวเตอร์ขนาดเล็กสำหรับโปรเจกต์ IoT"
            )
            self.ids.product_image.source = 'https://www.raspberrypi.com/assets/img/rp4.png'
            self.ids.status_label.text = 'พบข้อมูลสินค้า'
        elif rfid_tag == "RFID67890":
            self.ids.product_info_label.text = (
                "ชื่อสินค้า: โมดูล RFID RC522\n"
                "จำนวน: 50\n"
                "รายละเอียด: โมดูลอ่าน/เขียน RFID สำหรับ Arduino/Raspberry Pi"
            )
            self.ids.product_image.source = 'https://assets.adafruit.com/blog/2012/12/rc522.jpg'
            self.ids.status_label.text = 'พบข้อมูลสินค้า'
        else:
            self.ids.product_info_label.text = 'ไม่พบสินค้าสำหรับ RFID Tag นี้'
            self.ids.product_image.source = ''
            self.ids.status_label.text = 'ไม่พบข้อมูล'


class ManageProductScreen(Screen):
    _captured_image_path = StringProperty('')

    def on_enter(self):
        # เคลียร์ฟอร์มเมื่อเข้ามาหน้านี้ใหม่
        self.ids.rfid_tag_input.text = ''
        self.ids.product_name_input.text = ''
        self.ids.quantity_input.text = ''
        self.ids.description_input.text = ''
        self.ids.captured_image.source = ''
        self._captured_image_path = ''


    def capture_photo(self):
        # --- โค้ดเชื่อมต่อกล้องจริง ---
        # บน Raspberry Pi:
        # try:
        #     camera = PiCamera()
        #     camera.resolution = (640, 480)
        #     import time
        #     time.sleep(2) # ให้กล้อง warm up
        #     file_path = '/tmp/captured_image.jpg' # ตำแหน่งบันทึกชั่วคราว
        #     camera.capture(file_path)
        #     camera.close()
        #     self._captured_image_path = file_path
        #     self.ids.captured_image.source = file_path
        #     self.ids.captured_image.reload() # บังคับให้โหลดรูปใหม่
        #     print(f"รูปภาพถูกบันทึกที่: {file_path}")
        # except Exception as e:
        #     print(f"เกิดข้อผิดพลาดในการถ่ายภาพ: {e}")

        # บน PC (ถ้าใช้ Webcam):
        # try:
        #     cap = cv2.VideoCapture(0) # 0 คือกล้อง default
        #     if not cap.isOpened():
        #         raise IOError("ไม่สามารถเปิดกล้องได้")
        #     ret, frame = cap.read()
        #     if ret:
        #         file_path = '/tmp/captured_image.jpg'
        #         cv2.imwrite(file_path, frame)
        #         self._captured_image_path = file_path
        #         self.ids.captured_image.source = file_path
        #         self.ids.captured_image.reload()
        #         print(f"รูปภาพถูกบันทsึกที่: {file_path}")
        #     cap.release()
        # except Exception as e:
        #     print(f"เกิดข้อผิดพลาดในการถ่ายภาพ: {e}")
        # ----------------------------

        # จำลองการถ่ายภาพ (สำหรับทดสอบโดยไม่มีกล้องจริง)
        dummy_image_path = "data/images/default_product.png"
        if os.path.exists(dummy_image_path):
            self._captured_image_path = dummy_image_path
            self.ids.captured_image.source = dummy_image_path
            self.ids.captured_image.reload()
            print(f"จำลองการถ่ายภาพ: {dummy_image_path}")
        else:
            print("ไม่พบรูปภาพจำลอง 'data/images/default_product.png' กรุณาสร้างไฟล์นี้เพื่อทดสอบ")


    def save_product(self):
        rfid_tag = self.ids.rfid_tag_input.text
        product_name = self.ids.product_name_input.text
        quantity = self.ids.quantity_input.text
        description = self.ids.description_input.text
        image_path = self._captured_image_path

        if not rfid_tag or not product_name or not quantity:
            print("กรุณากรอกข้อมูลที่จำเป็น: RFID Tag, ชื่อสินค้า, จำนวน")
            # TODO: แสดง Pop-up แจ้งเตือนผู้ใช้
            return

        product_data = {
            "rfid_tag": rfid_tag,
            "name": product_name,
            "quantity": int(quantity),
            "description": description
        }

        print("ข้อมูลที่จะส่ง:", product_data)
        if image_path:
            print(f"มีรูปภาพ: {image_path}")
            # --- โค้ดเรียก Django API สำหรับบันทึกข้อมูลและอัปโหลดรูป ---
            # import requests
            # files = None
            # if image_path:
            #     files = {'image': open(image_path, 'rb')}
            # try:
            #     response = requests.post(
            #         'http://your-aws-api.com/api/products/',
            #         data=product_data,
            #         files=files
            #     )
            #     if response.status_code in [200, 201]:
            #         print("บันทึกสินค้าสำเร็จ!")
            #         # TODO: แสดง Pop-up "บันทึกสำเร็จ"
            #         self.manager.current = 'menu_screen' # กลับหน้าหลัก
            #     else:
            #         print(f"เกิดข้อผิดพลาดในการบันทึก: {response.status_code}, {response.text}")
            #         # TODO: แสดง Pop-up "บันทึกไม่สำเร็จ"
            # except requests.exceptions.RequestException as e:
            #     print(f"เกิดข้อผิดพลาดในการเชื่อมต่อ API: {e}")
            #     # TODO: แสดง Pop-up "ข้อผิดพลาดการเชื่อมต่อ"
            # finally:
            #     if files and 'image' in files:
            #         files['image'].close() # ปิดไฟล์หลังจากใช้งาน
            # -------------------------------------------------------------
        else:
            print("ไม่มีรูปภาพ (ส่งข้อมูลโดยไม่แนบรูป)")
            # โค้ดเรียก API ที่ไม่มีรูปภาพ (POST/PUT product_data อย่างเดียว)

        # หลังจากบันทึกเสร็จ (ในกรณีจำลอง)
        print("บันทึกสินค้า (จำลอง) สำเร็จ!")
        # TODO: แสดง Pop-up "บันทึกสำเร็จ"
        self.manager.current = 'menu_screen' # กลับหน้าหลัก

class ProductListScreen(Screen):
    def on_enter(self):
        # โหลดรายการสินค้าทุกครั้งที่เข้าหน้านี้
        self.load_products()

    def load_products(self):
        # ล้างรายการเก่า
        self.ids.product_list_grid.clear_widgets()

        # --- โค้ดเรียก Django API เพื่อดึงรายการสินค้าทั้งหมด ---
        # import requests
        # try:
        #     response = requests.get('http://your-aws-api.com/api/products/')
        #     if response.status_code == 200:
        #         products = response.json()
        #         for product in products:
        #             self.add_product_to_list(product)
        #     else:
        #         print(f"ข้อผิดพลาดในการโหลดรายการสินค้า: {response.status_code}")
        # except requests.exceptions.RequestException as e:
        #     print(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
        # ------------------------------------------------------

        # ตัวอย่างข้อมูลจำลอง
        dummy_products = [
            {"rfid_tag": "RFID12345", "name": "Raspberry Pi 4 Model B", "quantity": 10, "description": "บอร์ดคอมพิวเตอร์", "image": "https://www.raspberrypi.com/assets/img/rp4.png"},
            {"rfid_tag": "RFID67890", "name": "โมดูล RFID RC522", "quantity": 50, "description": "โมดูลอ่าน/เขียน RFID", "image": "https://assets.adafruit.com/blog/2012/12/rc522.jpg"},
            {"rfid_tag": "RFIDABCDE", "name": "เซ็นเซอร์อุณหภูมิ DHT11", "quantity": 100, "description": "สำหรับวัดอุณหภูมิและความชื้น", "image": "https://cdn-shop.adafruit.com/1200x900/386-00.jpg"}
        ]
        for product in dummy_products:
            self.add_product_to_list(product)

        # ปรับขนาด grid layout ให้พอดีกับเนื้อหา
        self.ids.product_list_grid.height = self.ids.product_list_grid.minimum_height


    def add_product_to_list(self, product):
        product_item_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(100), spacing=dp(10), padding=dp(5))
        product_item_layout.add_widget(Image(source=product.get('image', ''), size_hint_x=0.2, allow_stretch=True, keep_ratio=True))

        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.8)
        info_layout.add_widget(Label(text=f"RFID: {product['rfid_tag']}", font_size=dp(18), halign='left', text_size=(dp(300), None)))
        info_layout.add_widget(Label(text=f"ชื่อ: {product['name']}", font_size=dp(18), halign='left', text_size=(dp(300), None)))
        info_layout.add_widget(Label(text=f"จำนวน: {product['quantity']}", font_size=dp(18), halign='left', text_size=(dp(300), None)))
        info_layout.add_widget(Label(text=f"รายละเอียด: {product['description']}", font_size=dp(15), halign='left', text_size=(dp(300), None)))

        product_item_layout.add_widget(info_layout)
        self.ids.product_list_grid.add_widget(product_item_layout)


# --- Main App ---
class InventoryApp(App):
    def build(self):
        # โหลดไฟล์ inventory.kv
        self.title = 'ระบบจัดการคลังสินค้า'
        Builder.load_file('inventory.kv') # <--- โหลดไฟล์ .kv ที่นี่

        # ตั้งค่าขนาดหน้าต่างสำหรับ PC เพื่อการพัฒนา
        if Window.width < dp(800):
             Window.size = (dp(800), dp(600))

        # ตั้งค่า Kivy ให้ใช้ keyboard layout ภาษาไทยที่สร้างขึ้น
        Config.set('kivy', 'keyboard_mode', 'dock') # ให้คีย์บอร์ดปรากฏเป็น dock
        Config.set('keyboard', 'layout', 'thai')
        print("ตั้งค่า Kivy ให้ใช้ keyboard layout 'thai' แล้ว")

        # Add these lines to verify
        print(f"Kivy keyboard mode: {Config.get('kivy', 'keyboard_mode')}")
        print(f"Kivy keyboard layout: {Config.get('keyboard', 'layout')}")
        
        sm = ScreenManager()
        sm.add_widget(MenuScreen())
        sm.add_widget(ScanRFIDScreen())
        sm.add_widget(ManageProductScreen())
        sm.add_widget(ProductListScreen())
        return sm

if __name__ == '__main__':
    # สร้างโฟลเดอร์สำหรับรูปภาพจำลอง ถ้ายังไม่มี
    if not os.path.exists('data/images'):
        os.makedirs('data/images')
        print("สร้างโฟลเดอร์ 'data/images' แล้ว")

    # สร้างไฟล์ keyboard layout ภาษาไทย (ควรทำแค่ครั้งเดียว)
    thai_keyboard_layout = {
        "base": [
            ["ๅ", "/", "-", "ภ", "ถ", "ุ", "ึ", "ค", "ต", "จ", "ข", "ช"],
            ["ๆ", "ไ", "ำ", "พ", "ะ", "ั", "ี", "ร", "น", "ย", "บล", "ฃ"],
            ["ฟ", "ห", "ก", "ด", "เ", "า", "ส", "ว", "ง", "ผ", "ป"],
            {"rows": [
                ["Shift", "อ", "ิ", "แ", "ใ", "่", "้", "๊", "็", "ษ", "ศ", "Enter"]
            ], "modes": ["shift", "alt"]}
        ],
        "shift": [
            ["+", "๑", "๒", "๓", "๔", "ู", "฿", "๕", "๖", "๗", "๘", "๙"],
            ["๐", "\"", "ฎ", "ฑ", "ธ", "ํ", "๊", "ณ", "ฯ", "ญ", "ฐ", ","],
            ["ฤ", "ฆ", "ฏ", "โ", "ฌ", "็", "๋", "ษ", "ศ", "ซ", ".", "/"],
            {"rows": [
                ["Shift", "ฉ", "ฮ", "ฺ", "์", "?", "\"", ":", "(", ")", ";", "Enter"]
            ], "modes": ["base", "alt"]}
        ],
        "alt": [
            ["~", "!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "_"],
            ["`", "|", "{", "}", "[", "]", "\\", "<", ">", "?", ",", "."],
            ["€", "£", "¥", "₩", "₹", "₱", "¢", "®", "©", "™", "♪"],
            {"rows": [
                ["Shift", "Alt", " ", " ", " ", " ", " ", " ", " ", " ", " ", "Enter"]
            ], "modes": ["base", "shift"]}
        ]
    }

    # บันทึกไฟล์ layout นี้
    # ตรวจสอบว่า App.get_running_app() มีค่าหรือไม่ก่อนเรียก user_data_dir
    # ในการรันครั้งแรก App.get_running_app() จะเป็น None จนกว่า App().run() จะถูกเรียก
    # ดังนั้นเราใช้ os.path.expanduser('~/.kivy') เป็น fallback
    kivy_data_dir = os.path.join(App.get_running_app().user_data_dir if App.get_running_app() else os.path.expanduser('~/.kivy'), 'keyboards')
    os.makedirs(kivy_data_dir, exist_ok=True)
    thai_layout_file = os.path.join(kivy_data_dir, 'thai.json')

    try:
        with open(thai_layout_file, 'w', encoding='utf-8') as f:
            json.dump(thai_keyboard_layout, f, ensure_ascii=False, indent=4)
        print(f"บันทึกไฟล์ Kivy keyboard layout ภาษาไทยไปที่: {thai_layout_file}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการบันทึก keyboard layout: {e}")
        print("โปรดตรวจสอบสิทธิ์การเขียนไฟล์ หรือสร้างไฟล์ด้วยตนเองในโฟลเดอร์ที่ระบุ")

    InventoryApp().run()