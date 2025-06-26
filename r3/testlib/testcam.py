import kivy
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
import cv2
import glob
import os
from datetime import datetime

from kivy.core.text import LabelBase

# ปิด virtual keyboard ของ OS
#Config.set('kivy', 'keyboard_mode', 'systemandmulti')

# ลงทะเบียนฟอนต์ เกษมณี (Kasemanee) โดยสมมติว่าไฟล์ฟอนต์เกษมณีชื่อ "Kasemanee-Regular.ttf"
LabelBase.register(name='FSarabun', fn_regular='THSarabunNew.ttf')

SAVE_DIR = './captured_images'
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# รายการกล้อง: 0 (CSI), 1 (USB) ปรับตามระบบของคุณ
CAMERA_LIST = [0, 1]
CAMERA_LABELS = ["CSI Camera", "USB Camera"]


class GalleryPopup(Popup):
    def __init__(self, image_files, **kwargs):
        super().__init__(title="ภาพที่บันทึกไว้", size_hint=(0.95, 0.95), **kwargs)
        self.image_files = image_files
        self.page = 0
        self.images_per_page = 8

        main_layout = BoxLayout(orientation='vertical')

        # พื้นที่แสดงภาพ
        self.grid = GridLayout(cols=4, spacing=5, size_hint_y=0.85)
        main_layout.add_widget(self.grid)

        # พื้นที่ปุ่ม
        btn_area = BoxLayout(size_hint_y=0.15)
        self.prev_btn = Button(text='⬅️ ก่อนหน้า', font_name='FSarabun')
        self.next_btn = Button(text='ถัดไป ➡️', font_name='FSarabun')
        self.prev_btn.bind(on_press=self.prev_page)
        self.next_btn.bind(on_press=self.next_page)
        btn_area.add_widget(self.prev_btn)
        btn_area.add_widget(self.next_btn)
        main_layout.add_widget(btn_area)

        self.content = main_layout

        self.update_gallery()

    def update_gallery(self):
        self.grid.clear_widgets()
        start = self.page * self.images_per_page
        end = start + self.images_per_page
        for img in self.image_files[start:end]:
            img_widget = Image(source=img, size_hint_y=None, height=140)
            self.grid.add_widget(img_widget)
        # ปุ่มก่อนหน้า/ถัดไป
        self.prev_btn.disabled = self.page == 0
        self.next_btn.disabled = end >= len(self.image_files)

    def prev_page(self, instance):
        if self.page > 0:
            self.page -= 1
            self.update_gallery()

    def next_page(self, instance):
        if (self.page + 1) * self.images_per_page < len(self.image_files):
            self.page += 1
            self.update_gallery()

class CamTestApp(App):
    def build(self):
        self.cam_idx = 0
        #self.capture = cv2.VideoCapture(CAMERA_LIST[self.cam_idx])
        self.capture = cv2.VideoCapture(CAMERA_LIST[self.cam_idx],cv2.CAP_V4L2)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        layout = BoxLayout(orientation='vertical')
        
        self.img = Image()
        layout.add_widget(self.img)
        
        control_layout = BoxLayout(size_hint_y=0.2)
        
        self.switch_btn = Button(text=f"Switch Camera ({CAMERA_LABELS[self.cam_idx]})", font_name='FSarabun')
        self.switch_btn.bind(on_press=self.switch_camera)
        control_layout.add_widget(self.switch_btn)
        
        self.save_btn = Button(text='บันทึกภาพ', font_name='FSarabun')
        self.save_btn.bind(on_press=self.capture_image)
        control_layout.add_widget(self.save_btn)
        
        self.show_btn = Button(text='ดูรูปที่บันทึกไว้', font_name='FSarabun')
        self.show_btn.bind(on_press=self.show_saved_images)
        control_layout.add_widget(self.show_btn)
        
        layout.add_widget(control_layout)
        
        self.fullscreen = True  # เริ่มเต็มหน้าจอ
        from kivy.core.window import Window
        Window.fullscreen = self.fullscreen
        
        Clock.schedule_interval(self.update, 1.0/30.0)
        return layout

    def update(self, dt):
        ret, frame = self.capture.read()
        if ret:
            #frame = cv2.flip(frame, -1)  # <<< เพิ่มบรรทัดนี้เพื่อกลับหัว
            buf = cv2.flip(frame,0).tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.img.texture = texture

    def switch_camera(self, instance):
        self.cam_idx = (self.cam_idx + 1) % len(CAMERA_LIST)
        self.capture.release()
        self.capture = cv2.VideoCapture(CAMERA_LIST[self.cam_idx])
        self.switch_btn.text = f"Switch Camera ({CAMERA_LABELS[self.cam_idx]})"

    def capture_image(self, instance):
        ret, frame = self.capture.read()
        if ret:
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(SAVE_DIR, f"{now}.jpg")
            cv2.imwrite(filename, frame)
            self.show_message(f"บันทึกภาพเรียบร้อย: {filename}")

    def show_saved_images(self, instance):
        files = sorted(glob.glob(os.path.join(SAVE_DIR, "*.jpg")), reverse=True)
        if files:
            popup = GalleryPopup(files)
            popup.open()
        else:
            self.show_message("ยังไม่มีภาพที่บันทึกไว้")
    '''
    def show_saved_images(self, instance):
        files = sorted(glob.glob(os.path.join(SAVE_DIR, "*.jpg")), reverse=True)
        if files:
            grid = GridLayout(cols=2, spacing=5, size_hint_y=None)
            grid.bind(minimum_height=grid.setter('height'))
            for img_path in files[:8]:  # แสดงภาพล่าสุด 8 ภาพ
                img_widget = Image(source=img_path, size_hint_y=None, height=120)
                grid.add_widget(img_widget)
            popup = Popup(title="ภาพที่บันทึกไว้", content=grid, size_hint=(0.9, 0.9))
            popup.open()
        else:
            self.show_message("ยังไม่มีภาพที่บันทึกไว้")
    '''        
    def show_message(self, msg):
        popup = Popup(title="Info", content=Button(text=msg), size_hint=(0.4, 0.2))
        popup.open()

if __name__ == '__main__':
    CamTestApp().run()