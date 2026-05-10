from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.clock import Clock
from api_client import api
import rfid_lib

class InspectionTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_location_id = None
        self.current_location_rfid = None
        self.scanned_inventories = []
        self.expected_items = []
        self.inventory_map = {}
        self.location_map = {}
        self.is_scanning = False
        self.is_popup_open = False

    def refresh_data(self):
        # โหลดข้อมูลสินค้ามาเก็บไว้ในหน่วยความจำเพื่อหาชื่อสินค้าตอนสแกน
        success, invs = api.get_inventories()
        if success:
            self.inventory_map = {inv['rfid_code']: inv for inv in invs if 'rfid_code' in inv}
            
        success_loc, locs = api.get_locations()
        if success_loc:
            self.location_map = {loc['rfid_code']: loc for loc in locs if 'rfid_code' in loc}

    def toggle_scanning(self):
        self.is_scanning = not getattr(self, 'is_scanning', False)
        if self.is_scanning:
            if 'ins_toggle_scan_btn' in self.ids:
                self.ids.ins_toggle_scan_btn.text = 'หยุดอ่าน (Stop Scan)'
                self.ids.ins_toggle_scan_btn.background_color = (1, 0.3, 0.3, 1)

            self.rfid_counter = rfid_lib.RFCounter() 
            self.rfid_counter.start_scan(self.on_tag_scanned)
        else:
            if 'ins_toggle_scan_btn' in self.ids:
                self.ids.ins_toggle_scan_btn.text = 'RFID Scan'
                self.ids.ins_toggle_scan_btn.background_color = (0.2, 0.6, 1, 1)
            
            if hasattr(self, 'rfid_counter'):
                self.rfid_counter.stop_scan()
                self.rfid_counter.show_summary()

    def set_location(self, loc, tag):
        success, data = api.get_tag_info(tag)
        if success and data.get('status') == 'found_location':
            loc = data['location']
            self.expected_items = data['items']
            self.current_location_id = loc['id']
            self.current_location_rfid = tag
            
            loc_name = loc.get('name', tag)
            if 'current_location_label' in self.ids:
                self.ids.current_location_label.text = f"สถานที่ปัจจุบัน: {loc_name} (มีสินค้าเดิม {len(self.expected_items)} ชิ้น)"
            
            # เคลียร์ข้อมูลการสแกนเก่า
            self.scanned_inventories = []
            if 'inspected_items_list' in self.ids:
                self.ids.inspected_items_list.clear_widgets()
            if 'inspection_result_label' in self.ids:
                self.ids.inspection_result_label.text = ""
            
            # เปิดให้สแกนสินค้า
            if 'inspect_inv_input' in self.ids:
                self.ids.inspect_inv_input.disabled = False
                def refocus(dt):
                    self.ids.inspect_inv_input.focus = True
                Clock.schedule_once(refocus, 0.1)
                
            if 'inspect_loc_input' in self.ids:
                self.ids.inspect_loc_input.text = ""
        else:
            if 'inspection_result_label' in self.ids:
                self.ids.inspection_result_label.text = "ไม่พบสถานที่นี้ในระบบ หรือไม่ได้ลงทะเบียนเป็น Location"
                self.ids.inspection_result_label.color = (1, 0, 0, 1)
            if 'inspect_loc_input' in self.ids:
                self.ids.inspect_loc_input.text = ""

    def show_location_change_popup(self, loc, tag):
        self.is_popup_open = True
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        loc_name = loc.get('name', tag)
        msg = Label(text=f"พบสถานที่ใหม่: {loc_name}\nคุณต้องการเปลี่ยนสถานที่หรือไม่?\n(ข้อมูลที่สแกนไปแล้วจะถูกล้าง)", font_name='Kanit', halign='center')
        content.add_widget(msg)
        
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btn_new = Button(text="เลือกสถานที่ใหม่", font_name='Kanit', background_color=(0.2, 0.8, 0.2, 1))
        btn_old = Button(text="ใช้อันเก่าต่อไป", font_name='Kanit', background_color=(0.5, 0.5, 0.5, 1))
        
        btn_layout.add_widget(btn_new)
        btn_layout.add_widget(btn_old)
        content.add_widget(btn_layout)
        
        popup = Popup(title="ยืนยันการเปลี่ยนสถานที่", title_font='Kanit', content=content, size_hint=(0.6, 0.4), auto_dismiss=False)
        
        def on_new(instance):
            popup.dismiss()
            self.is_popup_open = False
            self.set_location(loc, tag)
            
        def on_old(instance):
            popup.dismiss()
            self.is_popup_open = False
            
        btn_new.bind(on_release=on_new)
        btn_old.bind(on_release=on_old)
        popup.open()

    def on_tag_scanned(self, tag):
        Clock.schedule_once(lambda dt: self._process_tag(tag))

    def _process_tag(self, tag):
        if getattr(self, 'is_popup_open', False):
            return
            
        tag = tag.strip()
        if not tag: return
        
        if tag in self.location_map:
            loc = self.location_map[tag]
            if not self.current_location_id:
                self.set_location(loc, tag)
            elif self.current_location_id != loc['id']:
                self.show_location_change_popup(loc, tag)
        elif tag in self.inventory_map:
            if not self.current_location_id:
                if 'inspection_result_label' in self.ids:
                    self.ids.inspection_result_label.text = "กรุณาสแกน Location ก่อน"
                    self.ids.inspection_result_label.color = (1, 0, 0, 1)
            else:
                if tag not in self.scanned_inventories:
                    self.scanned_inventories.append(tag)
                    inv = self.inventory_map[tag]
                    name = inv.get('name', 'สินค้าใหม่/ไม่รู้จัก')
                    if 'inspected_items_list' in self.ids:
                        lbl = Label(text=f"{len(self.scanned_inventories)}. {name} (RFID: {tag})", size_hint_y=None, height=30, halign='left', font_name='Kanit')
                        lbl.bind(size=lbl.setter('text_size'))
                        self.ids.inspected_items_list.add_widget(lbl)

    def on_location_scanned(self, text):
        tags = [t.strip() for t in text.replace(',', '\n').splitlines() if t.strip()]
        for tag in tags:
            self._process_tag(tag)
            
        if 'inspect_loc_input' in self.ids:
            self.ids.inspect_loc_input.text = ""

    def on_inventory_scanned(self, text):
        # 3. ทำการ scan tag สินค้าทั้งหมด
        tags = [t.strip() for t in text.replace(',', '\n').splitlines() if t.strip()]
        
        for tag in tags:
            self._process_tag(tag)
            
        if 'inspect_inv_input' in self.ids:
            self.ids.inspect_inv_input.text = ""
            def refocus(dt):
                self.ids.inspect_inv_input.focus = True
            Clock.schedule_once(refocus, 0.1)

    def submit_inspection(self):
        if not self.current_location_id:
            if 'inspection_result_label' in self.ids:
                self.ids.inspection_result_label.text = "กรุณาสแกน Location ก่อน"
                self.ids.inspection_result_label.color = (1, 0, 0, 1)
            return
            
        # 4. ประมวลผลว่า scan ได้ครบไหม หายไปกี่ตัว มีสินค้าใหม่กี่ตัว
        # คำนวณเบื้องต้นที่ฝั่ง Kivy
        expected_rfids = [item.get('rfid_code') for item in self.expected_items if item.get('rfid_code')]
        scanned_set = set(self.scanned_inventories)
        expected_set = set(expected_rfids)
        
        missing_rfids = expected_set - scanned_set
        extra_rfids = scanned_set - expected_set
        found_expected_rfids = scanned_set & expected_set
        
        # ค้นหา Object สินค้าที่หายไป / เกินมา
        missing_items = [item for item in self.expected_items if item.get('rfid_code') in missing_rfids]
        extra_items = [self.inventory_map[tag] for tag in extra_rfids if tag in self.inventory_map]
        
        # 5. ทำการ update last_location ของ สินค้าแต่ละตัวให้เป็นปัจจุบัน
        found_inventory_ids = []
        for tag in self.scanned_inventories:
            if tag in self.inventory_map:
                inv = self.inventory_map[tag]
                found_inventory_ids.append(inv['id'])
                # อัปเดต Location ให้เป็นปัจจุบันด้วย PATCH
                api.update_inventory(
                    inventory_id=inv['id'],
                    rfid_tag_id=inv.get('rfid_tag'),
                    rfid_code=tag,
                    name=inv.get('name'),
                    detail=inv.get('detail'),
                    current_location=self.current_location_id
                )

        # ส่งบันทึกประวัติการตรวจสอบไปที่ API
        success, res = api.submit_inspection(self.current_location_id, found_inventory_ids, self.scanned_inventories)
        
        # แสดงผลสรุป
        if 'inspection_result_label' in self.ids:
            msg = f"สรุปผล: จำนวนสินค้าเดิม {len(expected_set)} | พบ {len(found_expected_rfids)} | หาย {len(missing_rfids)} | สินค้าใหม่ {len(extra_rfids)}"
            self.ids.inspection_result_label.text = msg
            self.ids.inspection_result_label.color = (0, 1, 0, 1)
        
        # โชว์รายละเอียดของหาย / ของเกิน ใน UI List
        if 'inspected_items_list' in self.ids:
            self.ids.inspected_items_list.clear_widgets()
            
            if missing_items:
                lbl_miss = Label(text=f"รายการที่หาย ({len(missing_items)} ชิ้น):", size_hint_y=None, height=30, halign='left', color=(1, 0.3, 0.3, 1), font_name='Kanit')
                lbl_miss.bind(size=lbl_miss.setter('text_size'))
                self.ids.inspected_items_list.add_widget(lbl_miss)
                for item in missing_items:
                    lbl = Label(text=f" - {item.get('name')} ({item.get('rfid_code')})", size_hint_y=None, height=30, halign='left', color=(1, 0.5, 0.5, 1), font_name='Kanit')
                    lbl.bind(size=lbl.setter('text_size'))
                    self.ids.inspected_items_list.add_widget(lbl)
                    
            if extra_items:
                lbl_ext = Label(text=f"รายการที่เกินมา/ย้ายมาใหม่ ({len(extra_items)} ชิ้น):", size_hint_y=None, height=30, halign='left', color=(0.3, 0.8, 1, 1), font_name='Kanit')
                lbl_ext.bind(size=lbl_ext.setter('text_size'))
                self.ids.inspected_items_list.add_widget(lbl_ext)
                for item in extra_items:
                    lbl = Label(text=f" - {item.get('name')} ({item.get('rfid_code')})", size_hint_y=None, height=30, halign='left', color=(0.5, 0.8, 1, 1), font_name='Kanit')
                    lbl.bind(size=lbl.setter('text_size'))
                    self.ids.inspected_items_list.add_widget(lbl)
        
        # Reset สำหรับรอบถัดไป
        self.current_location_id = None
        self.current_location_rfid = None
        self.expected_items = []
        if 'current_location_label' in self.ids:
            self.ids.current_location_label.text = "สถานที่ปัจจุบัน: ยังไม่ได้เลือก"
        if 'inspect_inv_input' in self.ids:
            self.ids.inspect_inv_input.disabled = True
        self.scanned_inventories = []
        
        # โหลดข้อมูลอัปเดตเพื่อรับรู้ location ใหม่
        self.refresh_data()
