import os
import platform
import string
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.image import AsyncImage
from kivy.lang import Builder
from api_client import api

# แทรกการตั้งค่า Template ของ Kivy เพื่อบังคับให้ FileChooser แสดงฟอนต์ไทย (Kanit)
Builder.load_string('''
[FileListEntry@FloatLayout+TreeViewNode]:
    locked: False
    entries: []
    path: ctx.path
    is_selected: self.path in ctx.controller().selection
    orientation: 'horizontal'
    size_hint_y: None
    height: '48dp'
    canvas.before:
        Color:
            rgba: 0.15, 0.15, 0.15, 1
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: (0.2, 0.6, 1, 0.3) if self.is_selected else (0, 0, 0, 0)
        Rectangle:
            pos: self.pos
            size: self.size
    Image:
        id: icon
        pos_hint: {'center_x': 0.05, 'center_y': 0.5}
        size_hint: None, None
        size: '24dp', '24dp'
        source: 'atlas://data/images/defaulttheme/filechooser_%s' % ('folder' if ctx.isdir else 'file')
    Label:
        id: filename
        text_size: self.width, None
        halign: 'left'
        shorten: True
        text: ctx.name
        font_name: 'Kanit'
        pos_hint: {'center_x': 0.55, 'center_y': 0.5}
''')

class InventoryTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.available_tags = {}  # format: {"rfid_code": id}
        self.inventories = {}     # format: {"rfid_code": inventory_data}
        self.selected_image_path = None

    def refresh_rfid_list(self):
        success, data = api.get_rfid_tags()
        if success:
            # Assume data is a list of dicts. We filter for those not used yet.
            # In a real scenario, the backend might filter this. We'll show all that are not locations for now.
            # Or assume we can see them all and select one.
            tags = [tag for tag in data if not tag.get('is_location', False)]
            self.available_tags = {tag['rfid_code']: tag['id'] for tag in tags}
            
            if self.available_tags:
                self.ids.rfid_spinner.values = list(self.available_tags.keys())
                self.ids.rfid_spinner.text = '--- เลือก RFID ---'
            else:
                self.ids.rfid_spinner.values = []
                self.ids.rfid_spinner.text = 'ไม่มี RFID ว่าง'
                
        # โหลดข้อมูล Inventory ทั้งหมดเพื่อไว้แสดงข้อมูลเดิมเวลาเลือกรหัส
        inv_success, inv_data = api.get_inventories()
        if inv_success:
            self.inventories = {inv['rfid_code']: inv for inv in inv_data if 'rfid_code' in inv}

    def on_rfid_select(self, spinner_text):
        """ฟังก์ชันนี้ถูกเรียกเมื่อผู้ใช้เลือก RFID จาก Dropdown"""
        if spinner_text in self.inventories:
            inv = self.inventories[spinner_text]
            self.ids.inv_name_input.text = inv.get('name', '')
            
            if 'inv_detail_input' in self.ids:
                self.ids.inv_detail_input.text = inv.get('detail', '')
            
            # หากมีข้อมูลรูปภาพ ให้แสดงรูปภาพแรก
            images = inv.get('images', [])
            if images and len(images) > 0 and 'inv_image' in self.ids:
                # ตรวจสอบว่าเป็น path สมบูรณ์ หรือ relative path
                image_url = images[0].get('image')
                if image_url:
                    if image_url.startswith('/'):
                        image_url = f"{api.base_url}{image_url}"
                    self.ids.inv_image.source = image_url
        else:
            self.ids.inv_name_input.text = ""
            if 'inv_detail_input' in self.ids:
                self.ids.inv_detail_input.text = ""
            if 'inv_image' in self.ids:
                self.ids.inv_image.source = ''
        
        # รีเซ็ต path รูปภาพที่ผู้ใช้อาจจะเลือกค้างไว้
        self.selected_image_path = None

    def choose_image(self):
        """เปิด Popup ให้ผู้ใช้เลือกรูปภาพจากเครื่อง"""
        content = BoxLayout(orientation='vertical', spacing=10)
        
        # 1. สร้าง Dropdown สำหรับเลือก Drive (กรณี Windows) หรือ Home (Linux)
        drives = []
        if platform.system() == 'Windows':
            # ข้าม Drive A และ B เพื่อหลีกเลี่ยงการสแกน Floppy Disk ซึ่งจะทำให้โปรแกรมค้างชั่วขณะ
            for letter in string.ascii_uppercase[2:]:
                drive = letter + ":/"
                if os.path.exists(drive):
                    drives.append(drive)
        else:
            drives = ['/', os.path.expanduser('~')]
            
        top_layout = BoxLayout(size_hint_y=None, height='40dp', spacing=10)
        drive_spinner = Spinner(
            text=drives[0] if drives else '/',
            values=drives,
            font_name='Kanit',
            size_hint_x=0.3
        )
        top_layout.add_widget(drive_spinner)
        content.add_widget(top_layout)

        # 2. Layout แนวนอนสำหรับแสดงรายชื่อไฟล์ และรูปภาพ Preview
        main_layout = BoxLayout(orientation='horizontal', spacing=10)
        
        filechooser = FileChooserListView(filters=['*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG'], path=drive_spinner.text, size_hint_x=0.6)
        preview_image = AsyncImage(source='', size_hint_x=0.4, allow_stretch=True, keep_ratio=True)
        
        main_layout.add_widget(filechooser)
        main_layout.add_widget(preview_image)
        content.add_widget(main_layout)
        
        # ผูก event เมื่อเลือก Drive ใหม่จาก Spinner ให้เปลี่ยน path ของ file chooser ตาม
        def on_drive_select(spinner, text):
            filechooser.path = text
        drive_spinner.bind(text=on_drive_select)
        
        # ผูก event เมื่อมีการคลิกเลือกไฟล์ ให้แสดงรูป Preview ทางขวา
        def on_file_select(chooser, selection):
            if selection and os.path.isfile(selection[0]):
                preview_image.source = selection[0]
            else:
                preview_image.source = ''
        filechooser.bind(selection=on_file_select)

        # 3. สร้างปุ่มบันทึกและยกเลิก
        btn_layout = BoxLayout(size_hint_y=None, height='40dp', spacing=10)
        select_btn = Button(text="เลือก", font_name='Kanit')
        cancel_btn = Button(text="ยกเลิก", font_name='Kanit')
        btn_layout.add_widget(select_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(title="เลือกรูปภาพ", title_font='Kanit', content=content, size_hint=(0.9, 0.9))
        
        def on_select(instance):
            if filechooser.selection:
                self.selected_image_path = filechooser.selection[0]
                if 'inv_image' in self.ids:
                    self.ids.inv_image.source = self.selected_image_path
            popup.dismiss()
            
        select_btn.bind(on_release=on_select)
        cancel_btn.bind(on_release=popup.dismiss)
        
        popup.open()

    def submit_inventory(self):
        selected_code = self.ids.rfid_spinner.text
        name = self.ids.inv_name_input.text
        detail = self.ids.inv_detail_input.text
        
        if selected_code not in self.available_tags or not name:
            return # Should show error
            
        tag_id = self.available_tags[selected_code]
        success, res = api.create_inventory(tag_id, name, detail, self.selected_image_path)
        
        if success:
            self.ids.inv_name_input.text = ""
            self.ids.inv_detail_input.text = ""
            self.selected_image_path = None
            if 'inv_image' in self.ids:
                self.ids.inv_image.source = ''
            self.refresh_rfid_list()
