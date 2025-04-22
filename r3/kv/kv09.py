from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=20, **kwargs)

        self.text_input = TextInput(
            font_size=40,
            multiline=True,
            hint_text='พิมพ์ข้อความที่นี่...',
            font_name='/usr/share/fonts/truetype/tlwg/Garuda.ttf'  # ใช้ฟอนต์ไทย
        )
        self.add_widget(self.text_input)

        self.button = Button(
            text='ทดสอบภาษาไทย',
            font_size=30,
            font_name='/usr/share/fonts/truetype/tlwg/Garuda.ttf'  # ใช้ฟอนต์ไทย
        )
        self.add_widget(self.button)

class KioskApp(App):
    def build(self):
        from kivy.core.window import Window
        Window.fullscreen = 'auto'
        return MainLayout()

if __name__ == '__main__':
    KioskApp().run()
