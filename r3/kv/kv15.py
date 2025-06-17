from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
import RPi.GPIO as GPIO

LED_PIN = 17  # ขา GPIO ที่ใช้

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        
        self.led_status = False
        
        self.button = Button(text="LED OFF", font_size=32)
        self.button.bind(on_press=self.toggle_led)
        
        self.add_widget(self.button)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(LED_PIN, GPIO.OUT)
        GPIO.output(LED_PIN, GPIO.LOW)

    def toggle_led(self, instance):
        self.led_status = not self.led_status
        GPIO.output(LED_PIN, GPIO.HIGH if self.led_status else GPIO.LOW)
        self.button.text = "LED ON" if self.led_status else "LED OFF"

    def on_stop(self):
        GPIO.cleanup()

class GPIOApp(App):
    def build(self):
        return MainLayout()

if __name__ == "__main__":
    GPIOApp().run()
