from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import AsyncImage
from kivy.lang import Builder
from kivy.clock import Clock
from api_client import api
import threading
from datetime import datetime, timezone

Builder.load_string('''
<DashboardTab>:
    orientation: 'vertical'
    padding: 10
    spacing: 10

    BoxLayout:
        size_hint_y: None
        height: 170
        orientation: 'vertical'
        padding: 10
        canvas.before:
            Color:
                rgba: 0.15, 0.15, 0.15, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        BoxLayout:
            size_hint_y: None
            height: 40
            Label:
                text: 'สรุปข้อมูลระบบ (Dashboard)'
                font_name: 'Kanit'
                color: (0.3, 0.8, 1, 1)
                bold: True
                text_size: self.size
                halign: 'left'
                valign: 'middle'
            Button:
                text: 'รีเฟรชข้อมูล (Refresh)'
                font_name: 'Kanit'
                size_hint_x: None
                width: 150
                background_color: (0.2, 0.6, 1, 1)
                on_release: root.refresh_data()
            
        GridLayout:
            cols: 2
            id: summary_grid
            Label:
                id: lbl_total_tags
                text: 'จำนวน RFID Tag ทั้งหมด: กำลังโหลด...'
                font_name: 'Kanit'
                halign: 'left'
                text_size: self.size
                markup: True
            Label:
                id: lbl_unassigned_tags
                text: 'Tag ว่าง (ยังไม่กำหนด): กำลังโหลด...'
                font_name: 'Kanit'
                halign: 'left'
                text_size: self.size
                markup: True
            Label:
                id: lbl_loc_tags
                text: 'จำนวน Tag สถานที่: กำลังโหลด...'
                font_name: 'Kanit'
                halign: 'left'
                text_size: self.size
                markup: True
            Label:
                id: lbl_inv_tags
                text: 'จำนวน Tag สินค้า: กำลังโหลด...'
                font_name: 'Kanit'
                halign: 'left'
                text_size: self.size
                markup: True
            Label:
                id: lbl_unscanned_inv
                text: 'สินค้าที่ยังไม่ได้สแกน (ไม่มี Location): กำลังโหลด...'
                font_name: 'Kanit'
                halign: 'left'
                text_size: self.size
                markup: True

    Label:
        text: 'รายการสินค้าทั้งหมดแยกตามสถานที่'
        font_name: 'Kanit'
        size_hint_y: None
        height: 30
        color: (0.3, 0.8, 1, 1)
        bold: True
        
    ScrollView:
        BoxLayout:
            id: items_container
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            spacing: 10
            padding: 10
''')

class DashboardTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def refresh_data(self):
        self.ids.items_container.clear_widgets()
        self.ids.items_container.add_widget(Label(text="กำลังโหลดข้อมูล...", font_name='Kanit', size_hint_y=None, height=40))
        threading.Thread(target=self._fetch_data, daemon=True).start()

    def _fetch_data(self):
        success_tags, tags = api.get_rfid_tags()
        success_locs, locs = api.get_locations()
        success_invs, invs = api.get_inventories()
        
        if success_tags and success_locs and success_invs:
            Clock.schedule_once(lambda dt: self._update_ui(tags, locs, invs))
        else:
            Clock.schedule_once(lambda dt: self._show_error())

    def _update_ui(self, tags, locs, invs):
        total_tags = len(tags)
        loc_tags = len(locs)
        inv_tags = len(invs)
        
        assigned_rfid = set([loc.get('rfid_code') for loc in locs] + [inv.get('rfid_code') for inv in invs])
        unassigned_tags = total_tags - len(assigned_rfid)
        
        unscanned_inv = [inv for inv in invs if not inv.get('current_location_detail')]
        
        self.ids.lbl_total_tags.text = f'จำนวน RFID Tag ทั้งหมด: [b][size=26][color=#00FF00]{total_tags}[/color][/size][/b] Tag'
        self.ids.lbl_unassigned_tags.text = f'Tag ว่าง (ยังไม่กำหนด): [b][size=26][color=#FFD700]{unassigned_tags}[/color][/size][/b] Tag'
        self.ids.lbl_loc_tags.text = f'จำนวน Tag สถานที่: [b][size=26][color=#00BFFF]{loc_tags}[/color][/size][/b] Tag'
        self.ids.lbl_inv_tags.text = f'จำนวน Tag สินค้า: [b][size=26][color=#00BFFF]{inv_tags}[/color][/size][/b] Tag'
        self.ids.lbl_unscanned_inv.text = f'สินค้าที่ยังไม่ได้สแกน (ไม่มี Location): [b][size=26][color=#FF4500]{len(unscanned_inv)}[/color][/size][/b] ชิ้น'
        
        self.ids.items_container.clear_widgets()
        
        items_by_loc = {}
        for inv in invs:
            loc_name = inv.get('current_location_detail', {}).get('name', 'ยังไม่ได้ตรวจสอบ (No Location)') if inv.get('current_location_detail') else 'ยังไม่ได้ตรวจสอบ (No Location)'
            if loc_name not in items_by_loc:
                items_by_loc[loc_name] = []
            items_by_loc[loc_name].append(inv)
            
        for loc_name, items in items_by_loc.items():
            lbl_loc = Label(text=f"สถานที่: {loc_name} ({len(items)} ชิ้น)", font_name='Kanit', size_hint_y=None, height=40, color=(0.5, 1, 0.5, 1), halign='left')
            lbl_loc.bind(size=lbl_loc.setter('text_size'))
            self.ids.items_container.add_widget(lbl_loc)
            
            # จัดเตรียมข้อมูลและคำนวณเวลาที่ห่างจากการสแกนล่าสุด
            decorated_items = []
            now_utc = datetime.now(timezone.utc)
            now_local = datetime.now()
            
            for item in items:
                val = item.get('last_seen_at')
                dt = None
                diff = None
                if val and val not in ('N/A', 'ยังไม่เคยตรวจสอบ'):
                    try:
                        s = val.replace('Z', '+00:00')
                        dt = datetime.fromisoformat(s)
                        # ตรวจสอบว่าเป็นเวลาแบบมี Timezone หรือไม่ เพื่อลบให้ตรงกับเวลาปัจจุบันที่ถูกต้อง
                        diff = (now_local - dt) if dt.tzinfo is None else (now_utc - dt)
                    except Exception:
                        try:
                            dt = datetime.strptime(val[:19], '%Y-%m-%dT%H:%M:%S')
                            diff = now_local - dt
                        except:
                            pass
                decorated_items.append({'item': item, 'dt': dt, 'diff': diff})
                
            # ฟังก์ชันเรียงลำดับ: กลุ่มที่ไม่เคยสแกนขึ้นก่อน (0), กลุ่มที่สแกนแล้วเรียงจากเวลาที่ทิ้งช่วงนานที่สุด (1)
            def sort_key(dec_item):
                if dec_item['dt'] is None:
                    return (0, 0)
                return (1, -dec_item['diff'].total_seconds())
                
            decorated_items.sort(key=sort_key)
            
            for dec_item in decorated_items:
                item = dec_item['item']
                dt = dec_item['dt']
                diff = dec_item['diff']
                
                item_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=70, spacing=10)
                
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
                    
                last_seen_display = item.get('last_seen_at', 'ยังไม่เคยตรวจสอบ')
                time_ago_str = ""
                    
                if dt and diff:
                    total_seconds = int(diff.total_seconds())
                    if total_seconds < 0: total_seconds = 0
                    days = total_seconds // 86400
                    hours = (total_seconds % 86400) // 3600
                    minutes = (total_seconds % 3600) // 60
                    time_ago_str = f" (ไม่ได้สแกนมา: {days} วัน {hours} ชั่วโมง {minutes} นาที)"
                    last_seen_display = last_seen_display.replace('T', ' ')[:16]
                else:
                    last_seen_display = "ยังไม่เคยตรวจสอบ"
                    time_ago_str = " (ไม่ได้สแกนมา: นานมาก/ไม่เคยเลย)"
                    
                item_text = f"  ชื่อ: {item.get('name', 'Unknown')} (RFID: {item.get('rfid_code', 'N/A')})\n  ตรวจสอบล่าสุด: {last_seen_display}{time_ago_str}"
                item_lbl = Label(text=item_text, font_name='Kanit', size_hint_x=0.8, halign='left', valign='middle')
                item_lbl.bind(size=item_lbl.setter('text_size'))
                item_layout.add_widget(item_lbl)
                
                self.ids.items_container.add_widget(item_layout)

    def _show_error(self):
        self.ids.items_container.clear_widgets()
        self.ids.items_container.add_widget(Label(text="เกิดข้อผิดพลาดในการดึงข้อมูลจาก Server", font_name='Kanit', size_hint_y=None, height=40, color=(1, 0, 0, 1)))