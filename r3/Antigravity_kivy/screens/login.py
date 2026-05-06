from kivy.uix.screenmanager import Screen
from api_client import api

class LoginScreen(Screen):
    def set_login_mode(self, mode):
        self.login_mode = mode
        if mode == 'Password':
            self.ids.credential_label.text = 'รหัสผ่าน (Password)'
            self.ids.credential_input.password = True
            
            # Show username field
            self.ids.username_container.opacity = 1
            self.ids.username_container.disabled = False
            self.ids.username_container.size_hint_y = 1
            self.ids.username_container.height = self.height * 0.5
        else:
            self.ids.credential_label.text = 'API Key'
            self.ids.credential_input.password = False
            
            # Hide username field
            self.ids.username_container.opacity = 0
            self.ids.username_container.disabled = True
            self.ids.username_container.size_hint_y = None
            self.ids.username_container.height = 0

    def do_login(self):
        mode = getattr(self, 'login_mode', 'Password')
        username = self.ids.username_input.text
        credential = self.ids.credential_input.text
        
        print(api.api_key)
        if mode == 'Password':
            if not username or not credential:
                self.ids.login_message.text = "กรุณากรอกข้อมูลให้ครบถ้วน"
                return
            self.ids.login_message.text = "กำลังเข้าสู่ระบบ..."
            success, message = api.login(username, credential)

        else:
            if not credential:
                self.ids.login_message.text = "กรุณากรอก API Key"
                return
            self.ids.login_message.text = "กำลังตรวจสอบ API Key..."
            success, message = api.login_api_key(credential)

        print(message)  # Debugging output
        if success:
            self.ids.login_message.text = ""
            self.ids.credential_input.text = ""
            # Move to main screen
            self.manager.current = 'main_tabs'
            # Initialize the main screen data
            self.manager.get_screen('main_tabs').initialize_tabs()
        else:
            self.ids.login_message.text = message

        print(message)  # Debugging output
