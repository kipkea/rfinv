import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
import requests

# Configuration
API_BASE_URL = "http://localhost:8000"

class Session:
    token = None

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        layout.add_widget(Label(text="ระบบจัดการสินค้า RFID (Django API)", font_size=32, color=(0.2, 0.6, 1, 1)))
        
        self.username_input = TextInput(hint_text="ชื่อผู้ใช้งาน", multiline=False, size_hint_y=None, height=50)
        self.password_input = TextInput(hint_text="รหัสผ่าน", multiline=False, password=True, size_hint_y=None, height=50)
        
        layout.add_widget(self.username_input)
        layout.add_widget(self.password_input)
        
        login_btn = Button(text="เข้าสู่ระบบ", size_hint_y=None, height=60, background_color=(0.2, 0.8, 0.2, 1))
        login_btn.bind(on_press=self.do_login)
        layout.add_widget(login_btn)
        
        self.error_label = Label(text="", color=(1, 0, 0, 1))
        layout.add_widget(self.error_label)
        self.add_widget(layout)

    def do_login(self, instance):
        try:
            res = requests.post(f"{API_BASE_URL}/api/login/", json={
                "username": self.username_input.text,
                "password": self.password_input.text
            })
            if res.status_code in [200, 201]:
                Session.token = res.json().get("token")
                self.manager.current = 'main'
            else:
                self.error_label.text = "เข้าสู่ระบบไม่สำเร็จ"
        except Exception as e:
            self.error_label.text = f"Error: {str(e)}"

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tabs = TabbedPanel(do_default_tab=False)
        
        # Tab 1: Import RFID
        self.tab1 = TabbedPanelItem(text="นำเข้า RFID")
        t1_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        t1_layout.add_widget(Label(text="สแกน RFID Tags (คั่นด้วย ,)", size_hint_y=None, height=40))
        self.rfid_input = TextInput(hint_text="TAG001, TAG002", size_hint_y=None, height=100)
        t1_layout.add_widget(self.rfid_input)
        import_btn = Button(text="นำเข้าข้อมูล", size_hint_y=None, height=60, background_color=(0.2, 0.6, 1, 1))
        import_btn.bind(on_press=self.import_rfids)
        t1_layout.add_widget(import_btn)
        self.import_status = Label(text="")
        t1_layout.add_widget(self.import_status)
        self.tab1.add_widget(t1_layout)
        
        # Tab 2: Inventory
        self.tab2 = TabbedPanelItem(text="ข้อมูลสินค้า")
        t2_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        self.item_rfid_id = TextInput(hint_text="ID ของ RFID Tag", size_hint_y=None, height=50)
        self.item_name = TextInput(hint_text="ชื่อสินค้า", size_hint_y=None, height=50)
        self.item_detail = TextInput(hint_text="รายละเอียด", size_hint_y=None, height=100)
        t2_layout.add_widget(self.item_rfid_id)
        t2_layout.add_widget(self.item_name)
        t2_layout.add_widget(self.item_detail)
        save_btn = Button(text="บันทึกสินค้า", size_hint_y=None, height=60, background_color=(0.2, 0.6, 1, 1))
        save_btn.bind(on_press=self.save_inventory)
        t2_layout.add_widget(save_btn)
        self.item_status = Label(text="")
        t2_layout.add_widget(self.item_status)
        self.tab2.add_widget(t2_layout)

        # Tab 3: Location
        self.tab3 = TabbedPanelItem(text="กำหนดตำแหน่ง")
        t3_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        self.loc_rfid_id = TextInput(hint_text="ID ของ RFID Tag", size_hint_y=None, height=50)
        self.loc_name = TextInput(hint_text="ชื่อตำแหน่ง", size_hint_y=None, height=50)
        t3_layout.add_widget(self.loc_rfid_id)
        t3_layout.add_widget(self.loc_name)
        save_loc_btn = Button(text="บันทึกตำแหน่ง", size_hint_y=None, height=60, background_color=(0.2, 0.6, 1, 1))
        save_loc_btn.bind(on_press=self.save_location)
        t3_layout.add_widget(save_loc_btn)
        self.loc_status = Label(text="")
        t3_layout.add_widget(self.loc_status)
        self.tab3.add_widget(t3_layout)

        # Tab 4: Inspection
        self.tab4 = TabbedPanelItem(text="ตรวจสอบ")
        t4_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        self.insp_loc_rfid = TextInput(hint_text="RFID ตำแหน่ง", size_hint_y=None, height=50)
        self.insp_items = TextInput(hint_text="RFID สินค้าที่พบ (คั่นด้วย ,)", size_hint_y=None, height=100)
        t4_layout.add_widget(self.insp_loc_rfid)
        t4_layout.add_widget(self.insp_items)
        run_btn = Button(text="เริ่มตรวจสอบ", size_hint_y=None, height=60, background_color=(1, 0.5, 0, 1))
        run_btn.bind(on_press=self.run_inspection)
        t4_layout.add_widget(run_btn)
        self.insp_result = Label(text="")
        t4_layout.add_widget(self.insp_result)
        self.tab4.add_widget(t4_layout)

        self.tabs.add_widget(self.tab1)
        self.tabs.add_widget(self.tab2)
        self.tabs.add_widget(self.tab3)
        self.tabs.add_widget(self.tab4)
        self.add_widget(self.tabs)

    def get_headers(self):
        headers = {}
        if Session.token:
            headers["Authorization"] = f"Bearer {Session.token}"
        return headers

    def import_rfids(self, instance):
        tags = [t.strip() for t in self.rfid_input.text.split(",") if t.strip()]
        count = 0
        for tag in tags:
            try:
                res = requests.post(f"{API_BASE_URL}/api/RFIDTags/", json={"rfid_code": tag}, headers=self.get_headers())
                if res.status_code in [200, 201]: count += 1
            except: pass
        self.import_status.text = f"นำเข้าสำเร็จ {count} รายการ"

    def save_inventory(self, instance):
        payload = {
            "rfid_tag": int(self.item_rfid_id.text),
            "name": self.item_name.text,
            "detail": self.item_detail.text
        }
        try:
            res = requests.post(f"{API_BASE_URL}/api/inventory/", json=payload, headers=self.get_headers())
            if res.status_code in [200, 201]: self.item_status.text = "บันทึกสำเร็จ"
        except: self.item_status.text = "เกิดข้อผิดพลาด"

    def save_location(self, instance):
        payload = {
            "rfid_tag": int(self.loc_rfid_id.text),
            "name": self.loc_name.text
        }
        try:
            res = requests.post(f"{API_BASE_URL}/api/Locations/", json=payload, headers=self.get_headers())
            if res.status_code in [200, 201]: self.loc_status.text = "บันทึกสำเร็จ"
        except: self.loc_status.text = "เกิดข้อผิดพลาด"

    def run_inspection(self, instance):
        found = [t.strip() for t in self.insp_items.text.split(",") if t.strip()]
        payload = {
            "location_rfid": self.insp_loc_rfid.text,
            "found_rfids": found
        }
        try:
            res = requests.post(f"{API_BASE_URL}/api/inspections/", json=payload, headers=self.get_headers())
            data = res.json()
            self.insp_result.text = data.get("message", "ตรวจสอบสำเร็จ")
        except: self.insp_result.text = "เกิดข้อผิดพลาด"

class RFIDApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == '__main__':
    RFIDApp().run()
