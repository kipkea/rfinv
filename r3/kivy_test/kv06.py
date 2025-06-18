# camera_app.py

import os
import time
import subprocess
from datetime import datetime
import threading

import cv2
import numpy as np
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.text import LabelBase
from kivy.uix.textinput import TextInput

import sounddevice as sd
import soundfile as sf

LabelBase.register(name="THSarabun", fn_regular="./assets/THSarabunNew.ttf")

PHOTO_DIR = 'photos'
VIDEO_DIR = 'videos'
os.makedirs(PHOTO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

KV = '''
ScreenManager:
    CameraSelectScreen:
    LiveScreen:
    GalleryScreen:

<CameraSelectScreen>:
    name: 'select'
    BoxLayout:
        orientation: 'vertical'
        Label:
            id: info_label
            text: ''
            font_name: 'THSarabun'
            font_size: 40
        Button:
            text: 'เลือกกล้อง USB'
            font_name: 'THSarabun'
            on_release: root.select_usb()
        Button:
            text: 'เลือกกล้อง Pi'
            font_name: 'THSarabun'
            on_release: root.select_pi()

<LiveScreen>:
    name: 'live'
    BoxLayout:
        orientation: 'vertical'
        Label:
            id: info_label
            text: ''
            font_name: 'THSarabun'
            font_size: 30
        Label:
            id: recording_status
            text: ''
            font_name: 'THSarabun'
            font_size: 40
            color: 1, 0, 0, 1
        Image:
            id: camera_image
        BoxLayout:
            size_hint_y: 0.1
            spacing: 10
            Button:
                text: '📷 ถ่ายภาพ'
                font_name: 'THSarabun'
                on_release: root.capture_image()
            Button:
                id: record_btn
                text: '🎥 เริ่มบันทึก'
                font_name: 'THSarabun'
                on_release: root.toggle_recording()
            Button:
                text: '🔁 เปลี่ยนกล้อง'
                font_name: 'THSarabun'
                on_release: root.switch_camera()
            Button:
                text: '🖼 ไปยังแกลเลอรี'
                font_name: 'THSarabun'
                on_release: app.root.current = 'gallery'

<GalleryScreen>:
    name: 'gallery'
    BoxLayout:
        orientation: 'vertical'
        ScrollView:
            GridLayout:
                id: gallery_grid
                cols: 1
                size_hint_y: None
                height: self.minimum_height
        BoxLayout:
            size_hint_y: 0.1
            Button:
                text: '🔙 กลับ'
                font_name: 'THSarabun'
                on_release: app.root.current = 'select'
            Button:
                text: '🗑 ลบทั้งหมด'
                font_name: 'THSarabun'
                on_release: root.confirm_delete_all()
'''

class CameraSelectScreen(Screen):
    def on_enter(self):
        self.ids.info_label.text = "เลือกกล้องที่ต้องการใช้งาน"

    def select_usb(self):
        self.manager.current = 'live'
        self.manager.get_screen('live').camera_type = 'usb'

    def select_pi(self):
        self.manager.current = 'live'
        self.manager.get_screen('live').camera_type = 'pi'


class LiveScreen(Screen):
    camera_type = StringProperty('usb')
    recording = BooleanProperty(False)
    video_writer = None
    audio_frames = []
    stream = None
    capture = None
    video_filename = None
    wav_filename = None

    def on_enter(self):
        self.ids.info_label.text = f"ใช้กล้อง: {self.camera_type.upper()}"
        self.init_camera()
        Clock.schedule_interval(self.update, 1 / 30)

    def on_leave(self):
        Clock.unschedule(self.update)
        if self.capture:
            self.release_camera()
        if self.recording:
            self.stop_recording()

    def init_camera(self):
        if self.capture:
            self.release_camera()

        if self.camera_type == 'usb':
            self.capture = cv2.VideoCapture(0)
        else:
            try:
                from picamera2 import Picamera2
                p = Picamera2()
                p.configure(p.create_preview_configuration())
                p.start()
                self.capture = p
            except:
                self.capture = cv2.VideoCapture(0)
                self.camera_type = 'usb'

    def release_camera(self):
        if self.capture:
            if self.camera_type == 'usb':
                self.capture.release()
            elif self.camera_type == 'pi':
                self.capture.release()
            self.capture = None

    def update(self, dt):
        if not self.capture:
            return
        ret, frame = False, None
        if self.camera_type == 'usb':
            ret, frame = self.capture.read()
        else:
            try:
                frame = self.capture.capture_array()
                ret = True
            except:
                ret = False
        if ret:
            buf = cv2.flip(frame, 0).tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.ids.camera_image.texture = texture
            if self.recording and self.video_writer:
                self.video_writer.write(cv2.resize(frame, (640, 480)))

    def capture_image(self):
        if not self.capture:
            return
        ret, frame = self.capture.read() if self.camera_type == 'usb' else (True, self.capture.capture_array())
        if not ret:
            return

        def save_with_name(instance):
            name = textinput.text.strip()
            if not name:
                popup.dismiss()
                return
            filename = f"{PHOTO_DIR}/{name}.jpg"
            cv2.imwrite(filename, frame)
            self.ids.info_label.text = f"ถ่ายภาพเก็บที่ {filename}"
            popup.dismiss()

        layout = BoxLayout(orientation='vertical', spacing=10)
        layout.add_widget(Label(text='ตั้งชื่อไฟล์ภาพ', font_name='THSarabun'))
        textinput = TextInput(multiline=False)
        layout.add_widget(textinput)
        layout.add_widget(Button(text='บันทึก', on_release=save_with_name))
        popup = Popup(title='ตั้งชื่อ', content=layout, size_hint=(0.7, 0.5))
        popup.open()

    def audio_callback(self, indata, frames, time, status):
        self.audio_frames.append(indata.copy())

    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def animate_recording_label(self, dt):
        self.ids.recording_status.text = '' if self.ids.recording_status.text else '● กำลังบันทึก'

    def start_recording(self):
        now = datetime.now()
        self.video_filename = f"{VIDEO_DIR}/video_{now.strftime('%Y%m%d_%H%M%S')}.avi"
        self.wav_filename = self.video_filename.replace('.avi', '.wav')
        self.video_writer = cv2.VideoWriter(self.video_filename, cv2.VideoWriter_fourcc(*'XVID'), 20, (640, 480))
        self.audio_frames = []

        try:
            self.stream = sd.InputStream(samplerate=48000, channels=1, callback=self.audio_callback)
            self.stream.start()
            self.ids.info_label.text = f"เริ่มบันทึกวิดีโอ {self.video_filename}"
        except:
            self.stream = None
            self.ids.info_label.text = "ไม่พบไมค์ บันทึกเฉพาะวิดีโอ"

        self.recording = True
        self.ids.record_btn.text = "⏹ หยุดบันทึก"
        Clock.schedule_interval(self.animate_recording_label, 0.5)

    def stop_recording(self):
        if not self.recording:
            return
        self.recording = False
        self.video_writer.release()
        if self.stream:
            self.stream.stop()
            self.stream.close()

        self.ids.record_btn.text = "🎥 เริ่มบันทึก"
        Clock.unschedule(self.animate_recording_label)
        self.ids.recording_status.text = ''

        if self.audio_frames:
            audio_data = np.concatenate(self.audio_frames, axis=0)
            sf.write(self.wav_filename, audio_data, 48000)

        threading.Thread(target=self.merge_audio_video, args=(self.video_filename, self.wav_filename)).start()

    def merge_audio_video(self, video_path, audio_path):
        output_path = video_path.replace('.avi', '_final.mp4')
        cmd = ['ffmpeg', '-y', '-i', video_path, '-i', audio_path, '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental', output_path]
        try:
            subprocess.run(cmd, check=True)
            self.update_info(f'รวมไฟล์เสร็จสิ้น: {output_path}')
        except Exception as e:
            print('Merge failed:', e)
            self.update_info('รวมไฟล์ล้มเหลว')

    @mainthread
    def update_info(self, text):
        self.ids.info_label.text = text

    def switch_camera(self):
        if self.recording:
            self.ids.info_label.text = "หยุดบันทึกก่อนเปลี่ยนกล้อง"
            return
        self.camera_type = 'pi' if self.camera_type == 'usb' else 'usb'
        self.init_camera()


class GalleryScreen(Screen):
    def on_enter(self):
        self.load_gallery()

    def load_gallery(self):
        grid = self.ids.gallery_grid
        grid.clear_widgets()
        files = sorted(os.listdir(PHOTO_DIR), reverse=True)
        for f in files:
            path = os.path.join(PHOTO_DIR, f)
            layout = BoxLayout(orientation='vertical', size_hint_y=None, height=260, padding=5, spacing=5)
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                img = AsyncImage(source=path, size_hint_y=None, height=180)
                layout.add_widget(img)
            label = Label(text=f"{f}\n{time.ctime(os.path.getmtime(path))}", size_hint_y=None, height=40, font_size='20sp', font_name='THSarabun')
            label.text_size = label.size
            layout.add_widget(label)

            if f.lower().endswith(('.mp4', '.avi')):
                btn = Button(text='▶ เล่นวิดีโอ', size_hint_y=None, height=40, font_name='THSarabun')
                btn.bind(on_release=lambda inst, p=path: self.play_video(p))
                layout.add_widget(btn)
            else:
                btn = Button(text='ลบ', size_hint_y=None, height=40, font_name='THSarabun')
                btn.bind(on_release=lambda inst, p=path: self.confirm_delete(p))
                layout.add_widget(btn)

            grid.add_widget(layout)

    def play_video(self, path):
        try:
            subprocess.Popen(['mpv', path])
        except Exception as e:
            print("เล่นวิดีโอล้มเหลว:", e)

    def confirm_delete(self, path):
        layout = BoxLayout(orientation='vertical', spacing=10)
        layout.add_widget(Label(text='ลบภาพนี้?', font_name='THSarabun', font_size='40sp'))
        btns = BoxLayout(spacing=10, size_hint_y=None, height=40)
        btn_yes = Button(text='ใช่', font_name='THSarabun')
        btn_no = Button(text='ไม่', font_name='THSarabun')
        btns.add_widget(btn_yes)
        btns.add_widget(btn_no)
        layout.add_widget(btns)
        popup = Popup(title='ยืนยันการลบ', content=layout, size_hint=(.6, .4))
        btn_yes.bind(on_release=lambda x: self.delete_image(path, popup))
        btn_no.bind(on_release=popup.dismiss)
        popup.open()

    def delete_image(self, path, popup):
        try:
            os.remove(path)
            self.load_gallery()
            popup.dismiss()
        except:
            popup.dismiss()

    def confirm_delete_all(self):
        layout = BoxLayout(orientation='vertical', spacing=10)
        layout.add_widget(Label(text='ลบทั้งหมด?', font_name='THSarabun'))
        btns = BoxLayout(spacing=10, size_hint_y=None, height=40)
        btn_yes = Button(text='ใช่', font_name='THSarabun')
        btn_no = Button(text='ไม่', font_name='THSarabun')
        btns.add_widget(btn_yes)
        btns.add_widget(btn_no)
        layout.add_widget(btns)
        popup = Popup(title='ยืนยันลบทั้งหมด', content=layout, size_hint=(.6, .4))
        btn_yes.bind(on_release=lambda x: self.delete_all_images(popup))
        btn_no.bind(on_release=popup.dismiss)
        popup.open()

    def delete_all_images(self, popup):
        for f in os.listdir(PHOTO_DIR):
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                os.remove(os.path.join(PHOTO_DIR, f))
        self.load_gallery()
        popup.dismiss()


class CameraApp(App):
    def build(self):
        Builder.load_string(KV)
        sm = ScreenManager()
        sm.add_widget(CameraSelectScreen(name='select'))
        sm.add_widget(LiveScreen(name='live'))
        sm.add_widget(GalleryScreen(name='gallery'))
        sm.current = 'select'
        return sm


if __name__ == '__main__':
    CameraApp().run()
