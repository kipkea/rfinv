import os
import requests
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.clock import Clock

from dotenv import load_dotenv
import telepot
from telepot.loop import MessageLoop

#####################################
# โหลดค่า environment จากไฟล์ .env
load_dotenv()

APISERVER = os.getenv("APISERVER")
key = os.getenv("key")

#telegram 
bot_token = os.getenv("bot_token")
bot_id = os.getenv("bot_id")
######################################

# โหลดไฟล์การออกแบบ (KV)
#Builder.load_file('login.kv')

class LoginScreen(Screen):          
    def do_login(self, username, password):
        # URL ของ Django API (ตรวจสอบ IP ให้ถูกต้อง)
        url = f"http://{APISERVER}/api/login/" 
        payload = {
            "username": username,
            "password": password
        }

        try:
            # ส่งคำขอแบบ POST
            response = requests.post(url, json=payload, timeout=5)
            
            if response.status_code == 200:
                print("Django Login Success!")
                self.manager.current = 'home'
            else:
                self.ids.error_label.text = "Username หรือ Password ไม่ถูกต้อง"
        
        except requests.exceptions.ConnectionError:
            self.ids.error_label.text = "เชื่อมต่อ Server ไม่ได้"            

class APIKeyScreen(Screen):
    def do_login_key(self, api_key):
        url = f"http://{APISERVER}/api/login/" 
        payload = {
            "api_key": api_key  # ส่ง key ไปแทน username/password
        }

        try:
            response = requests.post(url, json=payload, timeout=5)
            
            # ต้องเช็ค status_code จาก Server
            if response.status_code == 200:
                print("API Key Validated!")
                # เคลียร์ข้อความ error ก่อนเปลี่ยนหน้า
                if 'key_error_label' in self.ids:
                    self.ids.key_error_label.text = ""                
                self.manager.current = 'home'
            else:
                # ตรวจสอบก่อนว่ามี id นี้จริงไหมเพื่อไม่ให้แอปเด้ง
                if 'key_error_label' in self.ids:
                    self.ids.key_error_label.text = "API Key ไม่ถูกต้อง"
                print(f"Login failed: {response.status_code}")
        
        except Exception as e:
            if 'key_error_label' in self.ids:
                self.ids.key_error_label.text = "Error: เชื่อมต่อไม่ได้"
            print(f"Connection Error: {e}")        
        

class HomeScreen(Screen):
    pass

class WindowManager(ScreenManager):
    pass

class LoginApp(App):
    def build(self):
        return WindowManager()

if __name__ == '__main__':
    LoginApp().run()