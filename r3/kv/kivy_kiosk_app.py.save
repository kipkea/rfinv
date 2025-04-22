from kivy.config import Config
# Kiosk: Fullscreen, disable escape
Config.set('graphics', 'fullscreen', 'auto')
Config.set('kivy', 'exit_on_escape', '0')
# Disable multi-touch mouse emulation for cleaner touch input
Config.set('input', 'mouse', 'mouse,disable_multitouch')

from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.textinput import TextInput
from kivy.uix.vkeyboard import VKeyboard
import os
from kivy.core.window import Window

# Optional: set a custom Thai font (ensure the .ttf is in your project folder)
THAI_FONT = 'THSarabunNew.ttf'

class KioskApp(App):
    def build(self):
        # Root layout
        root = BoxLayout(orientation='vertical')
        # Tabbed panel without default tab
        tp = TabbedPanel(do_default_tab=False)

        # -- Tab 1: Image and Button --
        tab1 = TabbedPanelItem(text='Tab 1')
        box1 = BoxLayout(orientation='vertical', padding=10, spacing=10)
        img1 = Image(source='image1.png', allow_stretch=True, keep_ratio=True)
        btn1 = Button(text='ปุ่ม Tab 1', size_hint=(1, None), height='50dp', font_size='20sp')
        btn1.bind(on_press=lambda x: print('Tab 1 pressed'))
        box1.add_widget(img1)
        box1.add_widget(btn1)
        tab1.add_widget(box1)
        tp.add_widget(tab1)

        # -- Tab 2: Spinner & Slider --
        tab2 = TabbedPanelItem(text='Settings')
        box2 = BoxLayout(orientation='vertical', padding=10, spacing=10)
        spinner = Spinner(
            text='ตัวเลือก 1',
            values=('ตัวเลือก 1', 'ตัวเลือก 2', 'ตัวเลือก 3'),
            size_hint=(1, None), height='50dp', font_size='18sp'
        )
        slider = Slider(min=0, max=100, value=50, size_hint=(1, None), height='50dp')
        box2.add_widget(spinner)
        box2.add_widget(slider)
        tab2.add_widget(box2)
        tp.add_widget(tab2)

        # -- Tab 3: Camera Capture --
        tab3 = TabbedPanelItem(text='Camera')
        box3 = BoxLayout(orientation='vertical', padding=10, spacing=10)
        cam = Camera(resolution=(640, 480), play=True)
        cap_btn = Button(text='Capture', size_hint=(1, None), height='50dp', font_size='20sp')
        cap_btn.bind(on_press=lambda x: self.capture(cam))
        box3.add_widget(cam)
        box3.add_widget(cap_btn)
        tab3.add_widget(box3)
        tp.add_widget(tab3)

        # -- Tab 4: TextInput + On-Screen Keyboard --
        tab4 = TabbedPanelItem(text='Keyboard')
        box4 = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.text_input = TextInput(
            font_name=THAI_FONT, font_size='24sp', size_hint=(1, None), height='100dp'
        )
        # VKeyboard: requires a layout file 'thai.json' in kivy/data/keyboard/
        vk = VKeyboard(layout='thai')
        vk.bind(on_key_up=self.on_key)
        box4.add_widget(self.text_input)
        box4.add_widget(vk)
        tab4.add_widget(box4)
        tp.add_widget(tab4)

        # -- Tab 5: Shutdown --
        tab5 = TabbedPanelItem(text='Shutdown')
        box5 = BoxLayout(orientation='vertical', padding=10, spacing=10)
        sd_btn = Button(
            text='Shutdown Now', background_color=(1, 0, 0, 1),
            size_hint=(1, None), height='50dp', font_size='20sp'
        )
        sd_btn.bind(on_press=lambda x: os.system('sudo shutdown now'))
        box5.add_widget(sd_btn)
        tab5.add_widget(box5)
        tp.add_widget(tab5)

        # Add to root
        root.add_widget(tp)
        return root

    def capture(self, camera_widget):
        # Save current frame as PNG
        texture = camera_widget.texture
        if texture:
            pixels = texture.pixels  # RGBA bytes
            size = texture.size
            # Convert to image via PIL
            try:
                from PIL import Image as PILImage
                import io
                img = PILImage.frombytes('RGBA', size, pixels)
                img.save('capture.png')
                print('Saved capture.png')
            except ImportError:
                print('Pillow not installed. Cannot save image.')

    def on_key(self, keyboard, keycode, *args):
        # Insert text or handle backspace
        if keycode[1] == 'backspace':
            self.text_input.do_backspace()
        else:
            self.text_input.insert_text(keycode[1])

if __name__ == '__main__':
    # Hide mouse cursor for touch kiosk
    Window.show_cursor = False
    KioskApp().run()
