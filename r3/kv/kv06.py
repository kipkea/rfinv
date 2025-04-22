from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemandmulti')  # ป้องกัน Virtual Keyboard OS เด้ง

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from keyboard_th import ThaiKeyboard

import sys

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=20, **kwargs)

        self.text_input = TextInput(font_size=40, multiline=True, hint_text='พิมพ์ข้อความที่นี่...')
        self.add_widget(self.text_input)

        self.exit_btn = Button(text='ออกจากโปรแกรม', size_hint_y=None, height=80, font_size=30, background_color=(1, 0, 0, 1))
        self.exit_btn.bind(on_release=self.exit_app)
        self.add_widget(self.exit_btn)

        self.keyboard = ThaiKeyboard(target_input=self.text_input, size_hint_y=0.6)
        self.add_widget(self.keyboard)

    def exit_app(self, instance):
        App.get_running_app().stop()
        sys.exit()

class KivyApp(App):
    def build(self):
        from kivy.core.window import Window
        Window.fullscreen = 'auto'
        return MainLayout()

if __name__ == '__main__':
    KivyApp().run()
