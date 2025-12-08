import json
from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.network.urlrequest import UrlRequest
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.uix.popup import Popup
from kivy.clock import mainthread
import subprocess
import threading

# --- ส่วน KV Language ---
KV_CODE = """
<ProductRow@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '60dp'
    padding: 5
    spacing: 5
    canvas.before:
        Color:
            rgba: 0.9, 0.9, 0.9, 1
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: root.index
        color: 0,0,0,1
        size_hint_x: 0.1
    Label:
        text: root.code
        color: 0,0,0,1
        size_hint_x: 0.2
    Label:
        text: root.desc
        color: 0,0,0,1
        size_hint_x: 0.3
        text_size: self.size
        halign: 'left'
        valign: 'middle'
        shorten: True
    Label:
        text: root.location
        color: 0,0,0,1
        size_hint_x: 0.15
    Label:
        text: root.date
        color: 0,0,0,1
        size_hint_x: 0.15
    AsyncImage:
        source: root.img_url
        size_hint_x: 0.1
        allow_stretch: True

<HeaderButton@Button>:
    background_normal: ''
    background_color: 0.3, 0.5, 0.7, 1
    bold: True

<MainLayout>:
    do_default_tab: False
    
    # --- Tab 1: Command Runner ---
    TabbedPanelItem:
        text: 'Command Runner'
        BoxLayout:
            orientation: 'vertical'
            padding: 10
            spacing: 10
            BoxLayout:
                size_hint_y: None
                height: '40dp'
                TextInput:
                    id: cmd_input
                    hint_text: 'Enter command...'
                    multiline: False
                    on_text_validate: root.run_command()
                Button:
                    text: 'Run'
                    size_hint_x: 0.2
                    on_press: root.run_command()
            TextInput:
                id: output_text
                text: 'Ready...'
                readonly: True
            Button:
                id: output_text
                text: 'Ready...'
                readonly: True

    # --- Tab 2: Product List (API) ---
    TabbedPanelItem:
        text: 'Products (API)'
        BoxLayout:
            orientation: 'vertical'
            padding: 5
            spacing: 5
            
            # ปุ่มโหลดข้อมูล
            Button:
                text: 'Load Data from API'
                size_hint_y: None
                height: '40dp'
                on_release: root.fetch_data()

            # ส่วนหัวตาราง (Headers) สำหรับกด Sort
            BoxLayout:
                size_hint_y: None
                height: '40dp'
                spacing: 2
                HeaderButton:
                    text: 'No.'
                    size_hint_x: 0.1
                    on_release: root.sort_data('index')
                HeaderButton:
                    text: 'Code'
                    size_hint_x: 0.2
                    on_release: root.sort_data('code')
                HeaderButton:
                    text: 'Description'
                    size_hint_x: 0.3
                    on_release: root.sort_data('desc')
                HeaderButton:
                    text: 'Location'
                    size_hint_x: 0.15
                    on_release: root.sort_data('location')
                HeaderButton:
                    text: 'Date'
                    size_hint_x: 0.15
                    on_release: root.sort_data('date')
                Label:
                    text: 'Image'
                    size_hint_x: 0.1
                    color: 0,0,0,1
                    canvas.before:
                        Color:
                            rgba: 0.8,0.8,0.8,1
                        Rectangle:
                            pos: self.pos
                            size: self.size

            # ตารางแสดงข้อมูล
            RecycleView:
                id: rv_products
                viewclass: 'ProductRow'
                RecycleBoxLayout:
                    default_size: None, dp(60)
                    default_size_hint: 1, None
                    size_hint_y: None
                    height: self.minimum_height
                    orientation: 'vertical'
                    spacing: 2
"""

Builder.load_string(KV_CODE)

class MainLayout(TabbedPanel):
    # เก็บสถานะการเรียงลำดับ (Ascending/Descending)
    sort_reverse = False
    
    # URL ของ Django API (ตัวอย่าง)
    #API_URL = 'http://127.0.0.1:8000/api/products/' 
    API_URL = 'http://localhost:8000/api/basic/'

    def show_exit_popup(self):
        """แสดง Popup ยืนยันการออกจากโปรแกรม"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_label = Label(text='Are you sure you want to exit?')
        
        buttons_layout = BoxLayout(size_hint_y=None, height='50dp', spacing=10)
        yes_button = Button(text='Yes')
        no_button = Button(text='No')
        buttons_layout.add_widget(yes_button)
        buttons_layout.add_widget(no_button)

        content.add_widget(popup_label)
        content.add_widget(buttons_layout)

        popup = Popup(title='Confirm Exit',
                      content=content,
                      size_hint=(None, None), size=(400, 200),
                      auto_dismiss=False)

        # กำหนดการทำงานของปุ่ม
        yes_button.bind(on_press=lambda *args: App.get_running_app().stop())
        no_button.bind(on_press=popup.dismiss)

        popup.open()


    def run_command(self):
        """ฟังก์ชันสำหรับ Tab 1 (Command Runner)"""
        command = self.ids.cmd_input.text
        if not command: return
        threading.Thread(target=self._execute_command, args=(command,), daemon=True).start()

    def _execute_command(self, command):
        try:
            process = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            result = process.stdout if process.returncode == 0 else process.stderr
        except Exception as e:
            result = str(e)
        self._update_cmd_output(result)

    @mainthread
    def _update_cmd_output(self, text):
        self.ids.output_text.text = text

    # --- ฟังก์ชันสำหรับ Tab 2 (Product API) ---

    def fetch_data(self):
        """เรียกข้อมูลจาก API ด้วย UrlRequest"""
        # หมายเหตุ: ในการใช้งานจริง เปลี่ยน API_URL เป็น URL ของคุณ
        # หากไม่มี Server จริง สามารถจำลองข้อมูลได้โดยข้ามไปเรียก self.on_api_success(req, mock_data)
        
        print(f"Fetching from {self.API_URL}...")
        
        # ใช้ UrlRequest เพื่อไม่ให้หน้าจอค้างขณะรอข้อมูล
        #UrlRequest(self.API_URL, on_success=self.on_api_success, on_failure=self.on_api_error, on_error=self.on_api_error)

        # *สำหรับการทดสอบหากไม่มี Server* ให้คอมเมนต์บรรทัดบนและใช้บรรทัดล่างนี้แทน:
        self.simulate_api_call()

    def on_api_success(self, req, result):
        """ทำงานเมื่อได้รับ JSON กลับมาสำเร็จ"""
        # สมมติว่า JSON ที่ได้เป็น List ของ Dict เช่น:
        # [{"id": 1, "code": "P001", "desc": "สินค้า A", "loc": "A1", "date": "2023-10-01", "img": "http..."}, ...]
        
        data_list = []
        for i, item in enumerate(result, 1):
            data_list.append({
                'index': str(i),
                'code': item.get('code', ''),
                'desc': item.get('desc', ''),
                'location': item.get('location', ''),
                'date': item.get('date', ''),
                'img_url': item.get('image_url', '') # URL รูปภาพ
            })
        
        # อัปเดตข้อมูลเข้า RecycleView
        self.ids.rv_products.data = data_list
        print("Data loaded successfully.")

    def on_api_error(self, req, error):
        print(f"API Error: {error}")
        # กรณี Error อาจแสดง Popup แจ้งเตือน

    def sort_data(self, key):
        """ฟังก์ชันเรียงลำดับข้อมูลเมื่อคลิกหัวตาราง"""
        data = self.ids.rv_products.data
        
        # สลับลำดับการเรียง (มากไปน้อย <-> น้อยไปมาก)
        self.sort_reverse = not self.sort_reverse
        
        # เรียงข้อมูลโดยใช้ Key ที่ส่งมา
        # ใช้ lambda เพื่อดึงค่าจาก dict ตาม key ที่ระบุ
        try:
            sorted_data = sorted(
                data, 
                key=lambda x: x[key], 
                reverse=self.sort_reverse
            )
            self.ids.rv_products.data = sorted_data
        except KeyError:
            print(f"Key {key} not found in data")

    def simulate_api_call(self):
        """ข้อมูลจำลองสำหรับทดสอบ (Mock Data)"""
        mock_data = [
            {'code': 'A001', 'desc': 'ปากกา', 'location': 'Shelf 1', 'date': '2023-10-01', 'image_url': 'https://cdmc.coj.go.th/cms/u1/20180611f9829f3a4145d4678f38a76d.png'},
            {'code': 'B002', 'desc': 'สมุดโน้ต', 'location': 'Shelf 2', 'date': '2023-09-15', 'image_url': 'https://cdmc.coj.go.th/cms/u1/20180611f9829f3a4145d4678f38a76d.png'},
            {'code': 'A003', 'desc': 'ดินสอ', 'location': 'Shelf 1', 'date': '2023-10-05', 'image_url': 'https://cdmc.coj.go.th/cms/u1/20180611f9829f3a4145d4678f38a76d.png'},
            {'code': 'C001', 'desc': 'ยางลบ', 'location': 'Shelf 3', 'date': '2023-08-20', 'image_url': 'https://cdmc.coj.go.th/cms/u1/20180611f9829f3a4145d4678f38a76d.png'},
        ]
        self.on_api_success(None, mock_data)

class KivyApp(App):
    def build(self):
        Window.bind(on_request_close=self.on_request_close)
        return MainLayout()

    def on_request_close(self, *args):
        """
        ถูกเรียกเมื่อผู้ใช้พยายามจะปิดหน้าต่าง (เช่น กดปุ่มกากบาท)
        เราจะแสดง popup ยืนยันแทนการปิดทันที
        """
        self.root.show_exit_popup()
        return True # คืนค่า True เพื่อบอก Kivy ว่าเราจัดการ event นี้แล้ว และไม่ต้องปิดหน้าต่าง


if __name__ == '__main__':
    KivyApp().run()