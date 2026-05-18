import platform
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.text import LabelBase
from kivy.core.window import Window
import os
import sys

from dotenv import load_dotenv

#####################################
# โหลดค่า environment จากไฟล์ .env
load_dotenv()

APISERVER = os.getenv("APISERVER")
key = os.getenv("key")

#telegram 
bot_token = os.getenv("bot_token")
bot_id = os.getenv("bot_id")

print("APISERVER:", APISERVER)
print("key:", key)
print("bot_token:", bot_token)
print("bot_id:", bot_id)
#################################

# Register Thai font
font_path = os.path.join('fonts', 'Kanit-Regular.ttf')
if os.path.exists(font_path):
    LabelBase.register(name='Kanit', fn_regular=font_path)

# Set window to be fullscreen, borderless, and non-resizable
from kivy.config import Config

Config.set('graphics', 'resizable', '1')
Config.set('graphics', 'borderless', '0')

#Config.set('graphics', 'resizable', '0')
#Config.set('graphics', 'borderless', '1')

# Apply Window settings
#Window.borderless = True
#Window.fullscreen = 'auto'
#Window.size = (1024, 768) # ปิดการตั้งค่าขนาดตายตัว เพราะเราใช้ Fullscreen แล้ว
Window.size = (800, 600) # ปิดการตั้งค่าขนาดตายตัว เพราะเราใช้ Fullscreen แล้ว

# Import screens
from screens.login import LoginScreen
from screens.main_tabs import MainTabScreen
from api_client import api

class RFIDApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screens = {}

    def build(self):
        from kivy.uix.floatlayout import FloatLayout
        from kivy.uix.button import Button

        # Load the KV file
        Builder.load_file('kv/app_layout.kv')
        
        # Create ScreenManager
        self.sm = ScreenManager()
        
        # Initialize screens
        self.screens['login'] = LoginScreen()
        self.screens['main_tabs'] = MainTabScreen()
        
        # Add screens to manager
        self.sm.add_widget(self.screens['login'])
        self.sm.add_widget(self.screens['main_tabs'])
        
        # Create a FloatLayout as the true root
        root_layout = FloatLayout()
        root_layout.add_widget(self.sm)
        
        # Add a universal close button at the top right
        close_btn = Button(
            text="X", 
            size_hint=(None, None), 
            size=(50, 50), 
            pos_hint={'right': 0.99, 'top': 0.99},
            background_color=(1, 0, 0, 0.8),
            color=(1, 1, 1, 1),
            font_size='24sp',
            bold=True
        )
        close_btn.bind(on_release=self.show_exit_popup)
        root_layout.add_widget(close_btn)
        
        return root_layout

    def show_exit_popup(self, instance):
        from kivy.uix.popup import Popup
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.label import Label
        
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        msg_label = Label(text='คุณต้องการทำสิ่งใด?', font_name='Kanit', font_size='20sp')
        content.add_widget(msg_label)
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.4)
        
        # สร้างปุ่ม 3 ตัวเลือก
        btn_exit = Button(text='ออกจากโปรแกรม', font_name='Kanit', background_color=(1, 0.3, 0.3, 1))
        btn_main = Button(text='กลับไปที่หน้า Login', font_name='Kanit', background_color=(0.2, 0.6, 1, 1))
        btn_cancel = Button(text='ยกเลิก', font_name='Kanit', background_color=(0.5, 0.5, 0.5, 1))
        
        btn_layout.add_widget(btn_exit)
        btn_layout.add_widget(btn_main)
        btn_layout.add_widget(btn_cancel)
        
        content.add_widget(btn_layout)
        
        popup = Popup(title='ยืนยัน', title_font='Kanit', content=content, size_hint=(0.6, 0.4), auto_dismiss=False)
        
        # ผูก Event คำสั่งให้ปุ่ม
        btn_exit.bind(on_release=lambda x: self.stop())
        btn_main.bind(on_release=lambda x: self.go_to_login(popup))
        btn_cancel.bind(on_release=popup.dismiss)
        
        popup.open()
        
    def go_to_login(self, popup):
        popup.dismiss()
        self.sm.current = 'login'

    def on_start(self):
        # ตรวจสอบว่าเป็น Raspberry Pi (Linux) หรือไม่
        if platform.system() == 'Linux':
            print("Detected Linux/Raspberry Pi. Attempting auto-login via API Key...")
            api_key = key
            print(api_key)
            success, message = api.login_api_key(api_key)
            print("success", success, message)
            if success:
                print("Auto-login successful.")
                self.sm.current = 'main_tabs'
                self.sm.get_screen('main_tabs').initialize_tabs()
            else:
                print(f"Auto-login failed: {message}")
                # บังคับออกจากโปรแกรมทันทีถ้าเป็น Raspberry Pi แล้ว Key ไม่ถูกต้อง
                self.stop()
                sys.exit(f"Exit: API Key is incorrect ({message})")
        else:
            print("Detected Windows/MacOS. Manual login required.")
            self.sm.current = 'login'

if __name__ == '__main__':
    RFIDApp().run()
