from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from threading import Thread
from keyboard_th import ThaiKeyboard

from gpiozero import Button as GPIOButton

# สร้าง GPIO ปุ่ม (เช่น ขา 17)
gpio_button = GPIOButton(17)

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=20, **kwargs)

        self.text_input = TextInput(font_size=40, multiline=True, hint_text='พิมพ์ข้อความที่นี่...')
        self.add_widget(self.text_input)

        self.keyboard = ThaiKeyboard(target_input=self.text_input, size_hint_y=0.6)
        self.add_widget(self.keyboard)

        # ตั้ง Interrupt ให้ GPIO ปุ่ม
        gpio_button.when_pressed = self.gpio_interrupt

    def gpio_interrupt(self):
        # เรียก Kivy UI ผ่าน thread-safe method
        Clock.schedule_once(lambda dt: self.text_input_insert())

    def text_input_insert(self):
        self.text_input.text += "\n[GPIO] ปุ่มจริงถูกกด!\n"

class KivyGPIOApp(App):
    def build(self):
        from kivy.core.window import Window
        Window.fullscreen = 'auto'  # โหมดเต็มจอ
        return MainLayout()

if __name__ == '__main__':
    # รันใน Thread หลัก
    KivyGPIOApp().run()
