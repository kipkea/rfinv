from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
import sys

# ตั้งค่าให้เต็มจอ Kiosk Mode
Window.fullscreen = 'auto'

# ฟอนต์ภาษาไทย
FONT_THAI = '/usr/share/fonts/truetype/tlwg/Garuda.ttf'

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
        if self.language == 'THAI':
            self.language = 'ENG'
        elif self.language == 'ENG':
            self.language = 'NUM'
        else:
            self.language = 'THAI'
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

        self.text_input = TextInput(font_size=40, font_name=FONT_THAI, hint_text='พิมพ์ข้อความที่นี่...', multiline=True)
        self.text_input.bind(focus=self.show_keyboard)
        self.add_widget(self.text_input)

        exit_btn = Button(text='ออกจากโปรแกรม', font_size=30, size_hint_y=None, height=80, background_color=(1,0,0,1), font_name=FONT_THAI)
        exit_btn.bind(on_release=self.exit_app)
        self.add_widget(exit_btn)

    def show_keyboard(self, instance, value):
        if value:
            if not any(isinstance(child, VirtualKeyboard) for child in self.children):
                self.add_widget(VirtualKeyboard(target_input=self.text_input))

    def exit_app(self, instance):
        App.get_running_app().stop()
        sys.exit()

class KioskApp(App):
    def build(self):
        return MainScreen()

if __name__ == '__main__':
    KioskApp().run()
