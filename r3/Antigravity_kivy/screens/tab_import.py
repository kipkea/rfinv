from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from api_client import api
from kivy.clock import Clock
import rfid_lib

class ImportTagTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scanned_tags = []
        self.is_scanning = False
        
    def toggle_scanning(self):
        self.is_scanning = not self.is_scanning
        if self.is_scanning:
            self.ids.toggle_scan_btn.text = 'หยุดอ่าน (Stop Scan)'
            self.ids.toggle_scan_btn.background_color = (1, 0.3, 0.3, 1)
            self.ids.rfid_scan_input.disabled = False
            self.ids.rfid_scan_input.focus = True

            # เริ่มการทำงานของโปรแกรมอ่าน RFID แบบต่อเนื่อง
            self.rfid_counter = rfid_lib.RFCounter() 
            self.rfid_counter.start_scan(self.on_tag_scanned)
                     
        else:
            self.ids.toggle_scan_btn.text = 'เริ่มอ่าน (Start Scan)'
            self.ids.toggle_scan_btn.background_color = (0.2, 0.6, 1, 1)
            self.ids.rfid_scan_input.disabled = False # เปิดให้กรอก Manual ได้เสมอ
            self.ids.rfid_scan_input.focus = False
            
            if hasattr(self, 'rfid_counter'):
                self.rfid_counter.stop_scan()
                self.rfid_counter.show_summary()

            # พอกดหยุดอ่าน ให้นำข้อมูลทั้งหมดที่อ่านได้ไปบันทึกอัตโนมัติ
            if self.scanned_tags:
                self.submit_tags()

    def on_tag_scanned(self, tag):
        # ให้ Kivy นำข้อมูลไปอัปเดตบนหน้าจอ (ต้องทำใน Main Thread)
        Clock.schedule_once(lambda dt: self._update_ui_with_tag(tag))
        
    def _update_ui_with_tag(self, tag):
        tag = tag.strip()
        if tag and tag not in self.scanned_tags:
            self.scanned_tags.append(tag)
            # Update UI list
            lbl = Label(text=f"{len(self.scanned_tags)}. {tag}", size_hint_y=None, height=30, halign='left')
            lbl.bind(size=lbl.setter('text_size'))
            self.ids.scanned_tags_list.add_widget(lbl)
            
            self.ids.scan_count_label.text = f'อ่านแล้ว: {len(self.scanned_tags)} รหัส'

    def add_scanned_tag(self, text):
        # แยกข้อความเผื่อผู้ใช้วางข้อมูลแบบ Manual หลายบรรทัดพร้อมกัน
        tags = [t.strip() for t in text.replace(',', '\n').splitlines() if t.strip()]
        
        for tag in tags:
            if tag not in self.scanned_tags:
                self.scanned_tags.append(tag)
                # Update UI list
                lbl = Label(text=f"{len(self.scanned_tags)}. {tag}", size_hint_y=None, height=30, halign='left')
                lbl.bind(size=lbl.setter('text_size'))
                self.ids.scanned_tags_list.add_widget(lbl)
                
        if tags:
            self.ids.scan_count_label.text = f'อ่านแล้ว: {len(self.scanned_tags)} รหัส'
            
        # ล้างช่องเพื่อรอรับข้อมูลถัดไป
        self.ids.rfid_scan_input.text = ""

        # ดึง Cursor กลับเข้าช่องอัตโนมัติเฉพาะตอนอยู่ในโหมด Start Scan (สแกนผ่าน USB)
        def refocus(dt):
            self.ids.rfid_scan_input.focus = True
        Clock.schedule_once(refocus, 0.1)

    def clear_tags(self):
        self.scanned_tags.clear()
        self.ids.scanned_tags_list.clear_widgets()
        self.ids.scan_count_label.text = 'อ่านแล้ว: 0 รหัส'

    def submit_tags(self):
        if not self.scanned_tags:
            return
            
        total_scanned = len(self.scanned_tags)
        success_count = 0
        duplicate_tags = []
        
        for tag in self.scanned_tags:
            #success, res = api.create_rfid_tag(tag, is_location=False)
            success, res = api.create_rfid_tag(tag)
            if success:
                success_count += 1
            else:
                print(res)
                # Check if the error is actually about duplication
                if "already exists" in str(res).lower() or "unique" in str(res).lower():
                    duplicate_tags.append(tag)
                else:
                    # Show the actual error message to the user
                    duplicate_tags.append(f"{tag} \n({res})")
                
        # Clear the original list UI
        self.clear_tags()
        
        # Display Summary
        summary_text = f"สรุปผล: นำเข้าทั้งหมด {total_scanned} | สำเร็จ {success_count} | ซ้ำ {len(duplicate_tags)}"
        lbl_summary = Label(text=summary_text, size_hint_y=None, height=40, color=(0.2, 1, 0.2, 1), font_size='18sp')
        self.ids.scanned_tags_list.add_widget(lbl_summary)
        
        if duplicate_tags:
            lbl_dup_title = Label(text="รายการรหัสที่ซ้ำ (มีอยู่ในระบบแล้ว):", size_hint_y=None, height=30, color=(1, 0.5, 0.5, 1))
            lbl_dup_title.bind(size=lbl_dup_title.setter('text_size'))
            lbl_dup_title.halign = 'left'
            self.ids.scanned_tags_list.add_widget(lbl_dup_title)
            
            for tag in duplicate_tags:
                print(tag)
                lbl_dup = Label(text=f" - {tag}", size_hint_y=None, height=30, color=(1, 0.3, 0.3, 1))
                lbl_dup.bind(size=lbl_dup.setter('text_size'))
                lbl_dup.halign = 'left'
                self.ids.scanned_tags_list.add_widget(lbl_dup)
