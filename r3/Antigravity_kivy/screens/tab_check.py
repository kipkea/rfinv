from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivy.lang import Builder
from api_client import api
import rfid_lib
import threading
from kivy.clock import Clock

Builder.load_string('''
<CheckTab>:
    orientation: 'vertical'
    padding: 10
    spacing: 10
    
    BoxLayout:
        size_hint_y: None
        height: 50
        Label:
            text: 'ตรวจสอบข้อมูล RFID:'
            size_hint_x: 0.3
            font_name: 'Kanit'
        Button:
            text: 'RFID'
            size_hint_x: 0.2
            background_color: (0.2, 0.6, 1, 1)
            font_name: 'Kanit'
            on_release: root.on_scan_button_click()                               
        TextInput:
            id: check_input
            hint_text: 'สแกนหรือพิมพ์รหัส RFID...'
            multiline: False
            font_name: 'Kanit'
            on_text_validate: root.on_rfid_entered(self.text)
        Button:
            text: 'ค้นหา'
            size_hint_x: 0.2
            background_color: (0.2, 0.6, 1, 1)
            font_name: 'Kanit'
            on_release: root.on_rfid_entered(check_input.text)
            
    ScrollView:
        BoxLayout:
            id: result_container
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            spacing: 10
            padding: 10
''')

class CheckTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scanned_tags = []

    def on_scan_button_click(self):
        # เปลี่ยนข้อความปุ่มเป็น "กำลังค้นหา..."
        threading.Thread(target=self._do_single_scan, daemon=True).start()

    def _do_single_scan(self):
        tag = rfid_lib.read_single_tag(timeout=0.1)    
        Clock.schedule_once(lambda dt: self._process_scanned_tag(tag))

    def _process_scanned_tag(self, tag):
        if tag:
            print(f"สแกนเจอ: {tag}")
            # นำ tag ไปประมวลผลต่อ

            self._get_tag_info(tag)   
        else:
            print("ไม่พบรหัส RFID")

    def _get_tag_info(self, rfid_code):
        self.ids.result_container.clear_widgets()
        self.ids.result_container.add_widget(Label(text="กำลังค้นหาข้อมูล...", font_name='Kanit', size_hint_y=None, height=40, color=(1, 1, 0, 1)))
        
        success, data = api.get_tag_info(rfid_code)
        self.ids.result_container.clear_widgets()
        
        if not success:
            self.ids.result_container.add_widget(Label(text=f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {data}", font_name='Kanit', size_hint_y=None, height=40, color=(1, 0, 0, 1)))
            return
            
        status = data.get('status')
        if status == 'not_found':
            self.show_not_found(rfid_code)
        elif status == 'found_inventory':
            self.show_inventory_info(data.get('inventory'), rfid_code)
        elif status == 'found_location':
            self.show_location_info(data.get('location'), data.get('items'), rfid_code)

    def on_rfid_entered(self, rfid_code):
        rfid_code = rfid_code.strip()
        if not rfid_code:
            return
        
        self._get_tag_info(rfid_code)    
    
    def show_not_found(self, rfid_code):
        lbl = Label(text=f"ไม่พบข้อมูลรหัส RFID: {rfid_code} ในระบบ", font_name='Kanit', size_hint_y=None, height=40, color=(1, 0, 0, 1))
        self.ids.result_container.add_widget(lbl)
        
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=20)
        btn_inv = Button(text="ลงทะเบียนเป็นสินค้าใหม่", font_name='Kanit', background_color=(0, 0.7, 0.9, 1))
        btn_inv.bind(on_release=lambda x: self.switch_to_register('inventory', rfid_code))
        
        btn_loc = Button(text="ลงทะเบียนเป็นสถานที่ใหม่", font_name='Kanit', background_color=(0, 0.9, 0, 1))
        btn_loc.bind(on_release=lambda x: self.switch_to_register('location', rfid_code))
        
        btn_layout.add_widget(btn_inv)
        btn_layout.add_widget(btn_loc)
        self.ids.result_container.add_widget(btn_layout)

    def show_inventory_info(self, inv, rfid_code):
        if not inv:
            self.ids.result_container.add_widget(Label(text=f"พบ Tag: {rfid_code} แต่ไม่พบรายละเอียดสินค้า", font_name='Kanit', size_hint_y=None, height=40, color=(1, 0.5, 0, 1)))
            return
            
        name = inv.get('name', 'N/A')
        detail = inv.get('detail', 'N/A')
        
        loc_detail = inv.get('current_location_detail')
        loc_name = loc_detail.get('name', 'N/A') if isinstance(loc_detail, dict) else 'N/A'
            
        last_seen = inv.get('last_seen_at', 'N/A')
        if last_seen and last_seen != 'N/A':
            last_seen = last_seen.replace('T', ' ')[:16] # ตัดเอาแค่วันและเวลา (เช่น 2026-05-07 12:00)
        
        info_text = f"ประเภท: สินค้า (Inventory)\nชื่อ: {name}\nรายละเอียด: {detail}\nสถานที่ปัจจุบัน: {loc_name}\nตรวจสอบล่าสุด: {last_seen}"
        lbl = Label(text=info_text, font_name='Kanit', size_hint_y=None, height=180, halign='left', valign='top')
        lbl.bind(size=lbl.setter('text_size'))
        self.ids.result_container.add_widget(lbl)
        
        # แสดงรูปภาพ (ตรวจสอบจากฟิลด์ image โดยตรง หรือ nested array ชื่อ images)
        image_url = None
        if inv.get('image') and isinstance(inv.get('image'), str):
            image_url = inv.get('image')
        elif inv.get('images') and isinstance(inv.get('images'), list) and len(inv.get('images')) > 0:
            image_url = inv.get('images')[0].get('image')
            
        if image_url:
            if image_url.startswith('/'):
                image_url = f"{api.base_url}{image_url}" # ต่อ URL ให้เต็มถ้า API ส่งมาแค่ Relative Path
            img = AsyncImage(
                source=image_url,
                size_hint_y=None,
                height=250,
                allow_stretch=True,
                keep_ratio=True
            )
            self.ids.result_container.add_widget(img)
        
    def show_location_info(self, loc, items, rfid_code):
        if not loc:
            self.ids.result_container.add_widget(Label(text=f"พบ Tag: {rfid_code} แต่ไม่พบรายละเอียดสถานที่", font_name='Kanit', size_hint_y=None, height=40, color=(1, 0.5, 0, 1)))
            return
            
        name = loc.get('name', 'N/A')
        desc = loc.get('description', 'N/A')
        
        info_text = f"ประเภท: สถานที่ (Location)\nชื่อ: {name}\nรายละเอียด: {desc}\nจำนวนสินค้าที่อยู่ที่นี่: {len(items)} รายการ\n"
        lbl = Label(text=info_text, font_name='Kanit', size_hint_y=None, height=120, halign='left', valign='top')
        lbl.bind(size=lbl.setter('text_size'))
        self.ids.result_container.add_widget(lbl)
        
        if items:
            self.ids.result_container.add_widget(Label(text="รายการสินค้า:", font_name='Kanit', size_hint_y=None, height=30, halign='left', color=(0.5, 1, 0.5, 1)))
            for i, item in enumerate(items, 1):
                item_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10)
                
                # 1. ดึงรูปภาพสินค้ามาแสดง
                image_url = None
                if item.get('image') and isinstance(item.get('image'), str):
                    image_url = item.get('image')
                elif item.get('images') and isinstance(item.get('images'), list) and len(item.get('images')) > 0:
                    image_url = item.get('images')[0].get('image')
                    
                if image_url:
                    if image_url.startswith('/'):
                        image_url = f"{api.base_url}{image_url}"
                    img = AsyncImage(source=image_url, size_hint_x=0.2, allow_stretch=True, keep_ratio=True)
                    item_layout.add_widget(img)
                else:
                    lbl_no_img = Label(text="[ไม่มีรูป]", font_name='Kanit', size_hint_x=0.2, color=(0.5, 0.5, 0.5, 1))
                    item_layout.add_widget(lbl_no_img)
                    
                # 2. แสดงรายละเอียดข้อความของสินค้า
                item_text = f"  {i}. {item.get('name', 'Unknown')} (RFID: {item.get('rfid_code', 'N/A')})"
                item_lbl = Label(text=item_text, font_name='Kanit', size_hint_x=0.8, halign='left', valign='middle')
                item_lbl.bind(size=item_lbl.setter('text_size'))
                item_layout.add_widget(item_lbl)
                
                self.ids.result_container.add_widget(item_layout)

    def switch_to_register(self, reg_type, rfid_code):
        self.ids.result_container.clear_widgets()
        self.ids.result_container.add_widget(Label(text="กำลังลงทะเบียน...", font_name='Kanit', size_hint_y=None, height=40, color=(1, 1, 0, 1)))
        
        success, res = api.create_rfid_tag(rfid_code, is_location=(reg_type == 'location'))
        
        self.ids.result_container.clear_widgets()
        if success:
            msg = f"ลงทะเบียน Tag สำเร็จ! โปรดไปที่แท็บ '{'สถานที่' if reg_type == 'location' else 'สินค้า'}' เพื่อกรอกข้อมูลต่อ"
            self.ids.result_container.add_widget(Label(text=msg, font_name='Kanit', size_hint_y=None, height=40, color=(0, 1, 0, 1)))
        else:
            self.ids.result_container.add_widget(Label(text=f"เกิดข้อผิดพลาดในการลงทะเบียน: {res}", font_name='Kanit', size_hint_y=None, height=40, color=(1, 0, 0, 1)))