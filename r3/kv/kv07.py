from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty
from kivy.config import Config
import sys
from kivy.core.text import LabelBase

# ปิด virtual keyboard ของ OS
Config.set('kivy', 'keyboard_mode', 'systemandmulti')

# ลงทะเบียนฟอนต์ Noto Sans Thai (ถ้าไม่ได้ใส่ฟอนต์เอง)
LabelBase.register(name='ThaiSaraban', fn_regular='THSarabunNew.ttf')

class MultiLangKeyboard(BoxLayout):
    layout_mode = NumericProperty(0)  # 0=ไทย, 1=อังกฤษ, 2=ตัวเลข

    def __init__(self, target_input, **kwargs):
        super().__init__(orientation='vertical', spacing=5, **kwargs)
        self.target = target_input

        self.language_btn = Button(text='สลับเป็น: ภาษาอังกฤษ', size_hint_y=None, height=70, font_size=30, font_name="ThaiSaraban")
        self.language_btn.bind(on_release=self.toggle_language)
        self.add_widget(self.language_btn)

        # ใช้ GridLayout สำหรับจัดปุ่ม
        self.keyboard_layout = GridLayout(cols=10, padding=10, spacing=5)
        self.add_widget(self.keyboard_layout)

        self.update_keyboard()

    def toggle_language(self, instance):
        self.layout_mode = (self.layout_mode + 1) % 3
        label = ["สลับเป็น: ภาษาอังกฤษ", "สลับเป็น: ตัวเลข", "สลับเป็น: ภาษาไทย"]
        self.language_btn.text = label[self.layout_mode]
        self.update_keyboard()

    def update_keyboard(self):
        self.keyboard_layout.clear_widgets()

        if self.layout_mode == 0:  # ภาษาไทย
            keys = ['ๆ','ไ','ำ','พ','ะ','ั','ี','ร','น','ย',
                    'บ','ล','ฃ','ฟ','ห','ก','ด','เ','้','่',
                    'า','ส','ว','ง','Backspace','Space','Enter']
        elif self.layout_mode == 1:  # อังกฤษ
            keys = ['q','w','e','r','t','y','u','i','o','p',
                    'a','s','d','f','g','h','j','k','l',
                    'z','x','c','v','b','n','m','Backspace','Space','Enter']
        else:  # ตัวเลข
            keys = ['1','2','3','4','5','6','7','8','9','0',
                    '-','/','(',')','฿','.','Backspace','Space','Enter']

        for key in keys:
            btn = Button(text=key, font_size=30, font_name="ThaiSaraban", size_hint_y=None, height=70)
            if key == 'Space':
                btn.text = 'เว้นวรรค'
                btn.bind(on_release=lambda x: self.insert_text(' '))
            elif key == 'Backspace':
                btn.text = 'ลบ'
                btn.bind(on_release=lambda x: self.backspace())
            elif key == 'Enter':
                btn.text = 'ขึ้นบรรทัดใหม่'
                btn.bind(on_release=lambda x: self.insert_text('\n'))
            else:
                btn.bind(on_release=lambda x, t=key: self.insert_text(t))
            self.keyboard_layout.add_widget(btn)

    def insert_text(self, substring):
        self.target.text += substring

    def backspace(self):
        self.target.text = self.target.text[:-1]

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=20, **kwargs)

        self.text_input = TextInput(font_size=40, multiline=True, hint_text='พิมพ์ข้อความที่นี่...', font_name="ThaiSaraban")
        self.add_widget(self.text_input)

        self.keyboard = MultiLangKeyboard(target_input=self.text_input, size_hint_y=0.6)
        self.add_widget(self.keyboard)

        self.exit_btn = Button(text='ออกจากโปรแกรม', size_hint_y=None, height=80, font_size=30, background_color=(1, 0, 0, 1), font_name="ThaiSaraban")
        self.exit_btn.bind(on_release=self.exit_app)
        self.add_widget(self.exit_btn)

    def exit_app(self, instance):
        App.get_running_app().stop()
        sys.exit()

class KioskApp(App):
    def build(self):
        from kivy.core.window import Window
        Window.fullscreen = 'auto'  # โหมด Kiosk
        return MainLayout()

if __name__ == '__main__':
    KioskApp().run()
