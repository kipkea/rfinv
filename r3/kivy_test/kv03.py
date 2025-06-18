import os
import cv2
import time
from kivy.app import App
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.image import AsyncImage

PHOTO_DIR = "photos"
if not os.path.exists(PHOTO_DIR):
    os.makedirs(PHOTO_DIR)

class CameraApp(App):
    def build(self):
        self.capture = cv2.VideoCapture(0)  # ใช้ PiCamera หรือ USB Webcam
        layout = BoxLayout(orientation='vertical')

        self.image_widget = Image()
        layout.add_widget(self.image_widget)

        btn_layout = BoxLayout(size_hint_y=0.15)
        capture_btn = Button(text='📸 ถ่ายภาพ')
        gallery_btn = Button(text='🖼 ดูภาพเก่า')

        capture_btn.bind(on_press=self.capture_image)
        gallery_btn.bind(on_press=self.show_gallery)

        btn_layout.add_widget(capture_btn)
        btn_layout.add_widget(gallery_btn)

        layout.add_widget(btn_layout)

        Clock.schedule_interval(self.update, 1.0 / 30.0)  # 30 FPS
        return layout

    def update(self, dt):
        ret, frame = self.capture.read()
        if ret:
            buf = cv2.flip(frame, 0).tostring()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.image_widget.texture = texture

    def capture_image(self, instance):
        ret, frame = self.capture.read()
        if ret:
            filename = f"{PHOTO_DIR}/photo_{int(time.time())}.jpg"
            cv2.imwrite(filename, frame)
            print(f"Saved: {filename}")

    def show_gallery(self, instance):
        popup_layout = GridLayout(cols=2, spacing=10, size_hint_y=None)
        popup_layout.bind(minimum_height=popup_layout.setter('height'))

        for filename in sorted(os.listdir(PHOTO_DIR), reverse=True):
            if filename.endswith(".jpg"):
                image_path = os.path.join(PHOTO_DIR, filename)
                img = AsyncImage(source=image_path, size_hint_y=None, height=200)
                popup_layout.add_widget(img)

        scroll = ScrollView()
        scroll.add_widget(popup_layout)

        popup = Popup(title='ภาพที่ถ่ายไว้', content=scroll, size_hint=(0.9, 0.9))
        popup.open()

    def on_stop(self):
        self.capture.release()

if __name__ == '__main__':
    CameraApp().run()





