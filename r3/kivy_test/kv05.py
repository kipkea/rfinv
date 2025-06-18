# kv04_full.py

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.properties import BooleanProperty
from kivy.uix.widget import Widget
import os
import cv2
import datetime

# ----------------------
# Hover + Touch Button
# ----------------------
class HoverBehavior(Widget):
    hovered = BooleanProperty(False)
    pressed = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)

    def on_mouse_pos(self, _, pos):
        if not self.get_root_window():
            return
        self.hovered = self.collide_point(*self.to_widget(*pos))

class HoverTouchButton(HoverBehavior, Button):
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.pressed = True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.pressed:
            self.pressed = False
        return super().on_touch_up(touch)

# ----------------------
# Screens
# ----------------------
class CameraSelectScreen(Screen):
    def select_usb(self):
        self.manager.current = 'live'

    def select_pi(self):
        self.manager.current = 'live'

class LiveScreen(Screen):
    def capture_image(self):
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"photo_{now}.jpg"
        path = os.path.join("images", filename)
        os.makedirs("images", exist_ok=True)
        frame = cv2.imread("test.jpg")  # simulate capture
        cv2.imwrite(path, frame)
        self.ids.info_label.text = f"ถ่ายภาพแล้ว: {filename}"

    def toggle_recording(self):
        self.ids.info_label.text = "กำลังบันทึกวิดีโอ..."

    def switch_camera(self):
        self.ids.info_label.text = "สลับกล้องเรียบร้อย"

class GalleryScreen(Screen):
    def confirm_delete_all(self):
        content = HoverTouchButton(
            text='ยืนยันลบทั้งหมด',
            on_release=lambda x: self.delete_all_images()
        )
        popup = Popup(title='ยืนยันการลบ', content=content, size_hint=(.6, .4))
        popup.open()

    def delete_all_images(self):
        folder = "images"
        for f in os.listdir(folder):
            os.remove(os.path.join(folder, f))
        self.ids.gallery_grid.clear_widgets()

# ----------------------
# App
# ----------------------
class CameraApp(App):
    def build(self):
        return Builder.load_file("camera.kv")

# ----------------------
# Run
# ----------------------
if __name__ == '__main__':
    CameraApp().run()
