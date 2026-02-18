import os
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivy.network.urlrequest import UrlRequest
import threading # เพิ่มการ import threading ไว้ด้านบน


# --- การตั้งค่าพื้นฐาน ---
#IPServer = "localhost"  
#IPServer = "10.35.116.201"  
IPServer = "192.168.1.13"  
API_URL = f"http://{IPServer}:8000/api/inventory/"
BASE_URL = f"http://{IPServer}:8000"
CACHE_DIR = "image_cache"

# สร้างโฟลเดอร์สำหรับเก็บรูปภาพถ้ายังไม่มี
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

"""
Widget พิเศษที่เช็คว่ามีรูปในเครื่องหรือยัง 
ถ้ามีแล้วจะดึงจากเครื่องมาแสดงทันทีเพื่อประหยัด Data และลดภาระ Server
"""
class CachedAsyncImage(AsyncImage):
    def __init__(self, **kwargs):
        self.original_source = kwargs.get('source', '')
        
        if self.original_source.startswith('http'):
            filename = self.original_source.split('/')[-1]
            self.local_path = os.path.join(CACHE_DIR, filename)
            
            if os.path.exists(self.local_path):
                kwargs['source'] = self.local_path
                print(f"DEBUG: Load from Cache -> {filename}")
            else:
                print(f"DEBUG: Need Download -> {self.original_source}")
                # แก้ไขตรงนี้: bind โดยไม่ต้องส่ง value
                self.bind(on_load=self._on_image_loaded)
        
        super().__init__(**kwargs)
        self.fit_mode = "contain"

    def _on_image_loaded(self, instance):
        """เมื่อโหลดเสร็จ ให้แยก Thread ไปบันทึกไฟล์เพื่อไม่ให้ UI กระตุก"""
        if not os.path.exists(self.local_path):
            # สร้าง Thread สำหรับการดาวน์โหลดและบันทึกไฟล์
            thread = threading.Thread(target=self._download_and_save)
            thread.daemon = True # ให้ thread จบการทำงานเมื่อปิดแอป
            thread.start()

    def _download_and_save(self):
        """ฟังก์ชันการทำงานใน Background Thread"""
        try:
            r = requests.get(self.original_source, stream=True, timeout=10)
            if r.status_code == 200:
                with open(self.local_path, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                print(f"DEBUG: Saved to Cache successfully -> {self.local_path}")
        except Exception as e:
            print(f"DEBUG: Cache Error (Background) -> {e}")
                

    def _save_to_cache(self, instance, value):
        """ทำงานเมื่อโหลดรูปจาก URL ครั้งแรกสำเร็จ"""
        if not os.path.exists(self.local_path):
            try:
                # ใช้ requests โหลดมาเขียนเป็นไฟล์เก็บไว้
                r = requests.get(self.original_source, stream=True)
                if r.status_code == 200:
                    with open(self.local_path, 'wb') as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)
                    print(f"DEBUG: Saved to Cache -> {self.local_path}")
            except Exception as e:
                print(f"DEBUG: Cache Error -> {e}")

class InventoryItem(BoxLayout):
    """Widget สำหรับแต่ละแถวในรายการสินค้า"""
    def __init__(self, item_data, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 120
        self.padding = 10
        self.spacing = 15

        # เตรียม URL รูปภาพ
        img_path = item_data.get('image', '')
        if img_path:
            full_img_url = BASE_URL + img_path
        else:
            full_img_url = "" # หรือใส่ path รูป default

        # ใช้ CachedAsyncImage แทน AsyncImage ปกติ
        img = CachedAsyncImage(source=full_img_url, size_hint_x=0.3)
        self.add_widget(img)

        # ส่วนรายละเอียดข้อความ
        details = BoxLayout(orientation='vertical')
        
        name_text = item_data.get('name', 'ไม่มีชื่อสินค้า')
        name_label = Label(
            text=f"[b]{name_text}[/b]", 
            markup=True, halign='left', valign='middle', font_size='18sp'
        )
        name_label.bind(size=name_label.setter('text_size'))
        
        # ดึงข้อมูล detail ออกมาดูก่อน ถ้าไม่มีให้เป็น Dictionary ว่าง {}
        loc_detail = item_data.get('current_location_detail')

        if loc_detail is not None:
            loc_name = loc_detail.get('name', 'ไม่ระบุชื่อสถานที่')
        else:
            loc_name = 'ไม่ระบุสถานที่'
            
        rfid_code = item_data.get('rfid_tag_detail', {}).get('rfid_code', '-')
        
        info_label = Label(
            text=f"สถานที่: {loc_name}\nRFID: {rfid_code}", 
            halign='left', valign='middle', color=(0.8, 0.8, 0.8, 1)
        )
        info_label.bind(size=info_label.setter('text_size'))

        details.add_widget(name_label)
        details.add_widget(info_label)
        self.add_widget(details)

class InventoryApp(App):
    def build(self):
        self.title = "RFID Inventory (Cached)"
        
        # Layout หลัก
        self.root_layout = BoxLayout(orientation='vertical')
        
        # ส่วนหัว
        header = Label(
            text="คลังสินค้า (ระบบ Cache รูปภาพ)", 
            size_hint_y=None, height=60, font_size='22sp', bold=True
        )
        self.root_layout.add_widget(header)

        # รายการแบบเลื่อนได้
        self.scroll = ScrollView()
        self.item_container = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.item_container.bind(minimum_height=self.item_container.setter('height'))
        
        self.scroll.add_widget(self.item_container)
        self.root_layout.add_widget(self.scroll)

        # ดึงข้อมูล
        self.fetch_api_data()
        
        return self.root_layout

    def fetch_api_data(self):
        print(f"API: Connecting {API_URL}...")
        UrlRequest(API_URL, on_success=self.on_api_success, on_error=self.on_api_error)

    def on_api_success(self, request, result):
        self.item_container.clear_widgets()
        for item in result:
            row = InventoryItem(item_data=item)
            self.item_container.add_widget(row)
        print(f"API: Loaded {len(result)} items.")

    def on_api_error(self, request, error):
        self.item_container.add_widget(Label(text="เกิดข้อผิดพลาดในการโหลดข้อมูล", color=(1,0,0,1)))

if __name__ == '__main__':
    InventoryApp().run()