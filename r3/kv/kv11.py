from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.core.window import Window
import sys
import requests
import cv2
import RPi.GPIO as GPIO
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from io import BytesIO
from PIL import Image as PILImage

# ตั้งค่าให้เต็มจอ Kiosk Mode
Window.fullscreen = 'auto'

# ฟอนต์ภาษาไทย
FONT_THAI = '/usr/share/fonts/truetype/tlwg/Garuda.ttf'

GPIO.setmode(GPIO.BCM)
GPIO_PIN = 17
GPIO.setup(GPIO_PIN, GPIO.OUT)

class VirtualKeyboard(BoxLayout):
    def __init__(self, target_input, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, height='350dp', **kwargs)
        self.target_input = target_input
        self.language = 'THAI'  # THAI, ENG, NUM
        self.shift = False
        self.capslock = False
        self.keys_area = BoxLayout(orientation='vertical', spacing=2, size_hint_y=0.8)
        self.add_widget(self.keys_area)
        self.build_keys()

        control = BoxLayout(size_hint_y=0.2)
        lang_btn = Button(text='สลับภาษา', font_name=FONT_THAI, on_release=self.switch_language)
        shift_btn = Button(text='Shift', font_name=FONT_THAI, on_release=self.toggle_shift)
        caps_btn = Button(text='CapsLock', font_name=FONT_THAI, on_release=self.toggle_capslock)
        hide_btn = Button(text='ซ่อนคีย์บอร์ด', font_name=FONT_THAI, on_release=lambda x: self.parent.remove_widget(self))
        control.add_widget(lang_btn)
        control.add_widget(shift_btn)
        control.add_widget(caps_btn)
        control.add_widget(hide_btn)

        self.add_widget(control)

    def build_keys(self):
        self.keys_area.clear_widgets()

        thai_normal = [
            ['ๆ', 'ไ', 'ำ', 'พ', 'ะ', 'ั', 'ี', 'ร', 'น', 'ย', 'บ', 'ล', 'ฃ'],
            ['ฟ', 'ห', 'ก', 'ด', 'เ', '้', '่', 'า', 'ส', 'ว', 'ง'],
            ['ผ', 'ป', 'แ', 'อ', 'ิ', 'ื', 'ท', 'ม', 'ใ', 'ฝ'],
            ['[ SPACE ]', '←']
        ]

        thai_shift = [
            ['+', '๑', '๒', '๓', '๔', 'ู', '฿', '๕', '๖', '๗', '๘', '๙', '๐', '"'],
            ['ฎ', 'ฑ', 'ธ', 'ํ', '๊', 'ณ', 'ฯ', 'ญ', 'ฐ'],
            ['ฤ', 'ฆ', 'ฏ', 'โ', 'ฌ', '็', '๋', 'ษ', 'ศ', 'ซ'],
            ['[ SPACE ]', '←']
        ]

        eng_normal = [
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
            ['z', 'x', 'c', 'v', 'b', 'n', 'm'],
            ['[ SPACE ]', '←']
        ]

        eng_shift = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M'],
            ['[ SPACE ]', '←']
        ]

        num_layout = [
            ['7', '8', '9'],
            ['4', '5', '6'],
            ['1', '2', '3'],
            ['0', '.', '←']
        ]

        if self.language == 'THAI':
            layout = thai_shift if self.shift else thai_normal
        elif self.language == 'ENG':
            layout = eng_shift if (self.shift or self.capslock) else eng_normal
        else:
            layout = num_layout

        for row in layout:
            row_layout = BoxLayout()
            for char in row:
                btn = Button(text=char, font_size=32, font_name=FONT_THAI)
                if char == '[ SPACE ]':
                    btn.bind(on_release=lambda btn: self.key_press(' '))
                elif char == '←':
                    btn.bind(on_release=lambda btn: self.backspace())
                else:
                    btn.bind(on_release=lambda btn: self.key_press(btn.text))
                row_layout.add_widget(btn)
            self.keys_area.add_widget(row_layout)

    def key_press(self, char):
        self.target_input.text += char
        if self.shift and not self.capslock:
            self.shift = False
            self.build_keys()

    def backspace(self):
        self.target_input.text = self.target_input.text[:-1]

    def switch_language(self, instance):
        self.language = {'THAI': 'ENG', 'ENG': 'NUM', 'NUM': 'THAI'}[self.language]
        self.build_keys()

    def toggle_shift(self, instance):
        self.shift = not self.shift
        self.build_keys()

    def toggle_capslock(self, instance):
        self.capslock = not self.capslock
        self.build_keys()

class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=20, **kwargs)

        # Tab Manager
        self.tabs = TabbedPanel()
        
        # Tab 1: Keyboard
        self.tab_keyboard = TabbedPanelItem(text='คีย์บอร์ด')
        self.tab_keyboard_content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.text_input = TextInput(font_size=40, font_name=FONT_THAI, hint_text='พิมพ์ข้อความที่นี่...', multiline=True)
        self.text_input.bind(focus=self.show_keyboard)
        self.tab_keyboard_content.add_widget(self.text_input)
        self.tab_keyboard.add_widget(self.tab_keyboard_content)

        # Tab 2: API
        self.tab_api = TabbedPanelItem(text='ส่งคำสั่ง API')
        send_btn = Button(text='ส่งข้อความ (API)', font_size=30, size_hint_y=None, height=80, background_color=(0,0.6,1,1), font_name=FONT_THAI)
        send_btn.bind(on_release=self.send_api)
        self.tab_api.add_widget(send_btn)

        # Tab 3: ถ่ายรูป
        self.tab_photo = TabbedPanelItem(text='ถ่ายรูป')
        photo_btn = Button(text='📷 ถ่ายรูป', font_size=30, size_hint_y=None, height=80, background_color=(0.2, 0.7, 0.2, 1), font_name=FONT_THAI)
        photo_btn.bind(on_release=self.capture_image)
        self.tab_photo.add_widget(photo_btn)

        # Tab 4: ล้างข้อความ
        self.tab_clear = TabbedPanelItem(text='ล้างข้อความ')
        clear_btn = Button(text='🧹 ล้างข้อความ', font_size=30, size_hint_y=None, height=80, background_color=(0.8, 0.8, 0.2, 1), font_name=FONT_THAI)
        clear_btn.bind(on_release=self.clear_text)
        self.tab_clear.add_widget(clear_btn)

        # Adding tabs to the main window
        self.tabs.add_widget(self.tab_keyboard)
        self.tabs.add_widget(self.tab_api)
        self.tabs.add_widget(self.tab_photo)
        self.tabs.add_widget(self.tab_clear)
        self.add_widget(self.tabs)

    def show_keyboard(self, instance, value):
        if value and not any(isinstance(child, VirtualKeyboard) for child in self.children):
            self.add_widget(VirtualKeyboard(target_input=self.text_input))

    def send_api(self, instance):
        message = self.text_input.text.strip()
        if not message:
            print('ข้อความว่างเปล่า ไม่สามารถส่งได้')
            return

        try:
            response = requests.post('http://your-api-server/endpoint', json={'message': message})
            if response.ok:
                print('ส่งข้อความเรียบร้อย:', response.json())
            else:
                print('ส่งข้อความล้มเหลว:', response.status_code, response.text)
        except Exception as e:
            print('เกิดข้อผิดพลาด:', e)

    def capture_image(self, instance):
        try:
            GPIO.output(GPIO_PIN, GPIO.HIGH)  # เปิดไฟ
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            GPIO.output(GPIO_PIN, GPIO.LOW)  # ปิดไฟ

            if ret:
                image_path = '/tmp/captured.jpg'
                cv2.imwrite(image_path, frame)

                # แสดงภาพบนจอ
                pil_image = PILImage.open(image_path)
                buf = BytesIO()
                pil_image.save(buf, format='png')
                buf.seek(0)
                self.image_display.texture = CoreImage(buf, ext='png').texture

                # ส่งผ่าน API
                with open(image_path, 'rb') as img_file:
                    files = {'file': ('captured.jpg', img_file, 'image/jpeg')}
                    response = requests.post('http://your-api-server/upload-image', files=files)
                    print('อัปโหลด:', response.status_code, response.text)

        except Exception as e:
            print('ถ่ายรูปผิดพลาด:', e)

    def clear_text(self, instance):
        self.text_input.text = ''

    def exit_app(self, instance):
        sys.exit()

class MyApp(App):
    def build(self):
        return MainScreen()

if __name__ == '__main__':
    MyApp().run()
