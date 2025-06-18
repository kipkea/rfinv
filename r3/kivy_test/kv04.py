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

LabelBase.register(name="THSarabun", fn_regular="./assets/THSarabunNew.ttf")


import sounddevice as sd
import soundfile as sf

PHOTO_DIR = 'photos'
VIDEO_DIR = 'videos'
os.makedirs(PHOTO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)


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
            except Exception as e:
                print('PiCamera ไม่พร้อมใช้งาน:', e)
                self.capture = cv2.VideoCapture(0)
                self.camera_type = 'usb'
        self.ids.info_label.text = f"ใช้กล้อง: {self.camera_type.upper()}"

    def release_camera(self):
        if self.capture is not None:
            if self.camera_type == 'usb':
                self.capture.release()
            elif self.camera_type == 'pi':
                #self.capture.close()
                self.capture.release()
            self.capture = None

    def switch_camera(self):
        if self.recording:
            self.ids.info_label.text = "หยุดบันทึกก่อนเปลี่ยนกล้อง"
            return
        if self.camera_type == 'usb':
            self.camera_type = 'pi'
        else:
            self.camera_type = 'usb'
        self.init_camera()

    def update(self, dt):
        frame = None
        ret = False
        if not self.capture:
            return

        if self.camera_type == 'usb':
            ret, frame = self.capture.read()
        else:
            try:
                frame = self.capture.capture_array()
                ret = True
            except Exception as e:
                ret = False
                print("Capture pi error:", e)

        if ret and frame is not None:
            h, w = frame.shape[:2]
            buf = cv2.flip(frame, 0).tobytes()
            texture = Texture.create(size=(w, h), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.ids.camera_image.texture = texture

            if self.recording and self.video_writer:
                resized = cv2.resize(frame, (640, 480))
                self.video_writer.write(resized)

    def capture_image(self):
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
        if ret and frame is not None:
            now = datetime.now()
            filename = f"{PHOTO_DIR}/photo_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(filename, frame)
            self.ids.info_label.text = f"ถ่ายภาพเก็บที่ {filename}"

    def audio_callback(self, indata, frames, time, status):
        self.audio_frames.append(indata.copy())

    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        now = datetime.now()
        self.video_filename = f"{VIDEO_DIR}/video_{now.strftime('%Y%m%d_%H%M%S')}.avi"
        self.wav_filename = self.video_filename.replace('.avi', '.wav')
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer = cv2.VideoWriter(self.video_filename, fourcc, 20, (640, 480))
        self.audio_frames = []

        try:
            self.stream = sd.InputStream(samplerate=48000, channels=1, callback=self.audio_callback)
            self.stream.start()
            self.ids.info_label.text = f"เริ่มบันทึกวิดีโอ {self.video_filename}"
        except Exception as e:
            self.ids.info_label.text = "ไม่พบไมค์โครโฟน: บันทึกเฉพาะวิดีโอ"
            print("Mic error:", e)
            self.stream = None

        self.recording = True
        self.ids.record_btn.text = "⏹ หยุดบันทึก"

    def stop_recording(self):
        if not self.recording:
            return
        self.recording = False
        self.video_writer.release()
        if self.stream:
            self.stream.stop()
            self.stream.close()

        self.ids.record_btn.text = "🎥 เริ่มบันทึก"
        self.ids.info_label.text = "บันทึกวิดีโอเสร็จสิ้น กำลังรวมไฟล์เสียงกับวิดีโอ..."

        # บันทึกเสียง wav
        if self.audio_frames:
            audio_data = np.concatenate(self.audio_frames, axis=0)
            sf.write(self.wav_filename, audio_data, 48000)
            print("บันทึกเสียงที่", self.wav_filename)

        # รัน ffmpeg รวมไฟล์เสียงกับวิดีโอใน thread
        threading.Thread(target=self.merge_audio_video, args=(self.video_filename, self.wav_filename)).start()

    def merge_audio_video(self, video_path, audio_path):
        output_path = video_path.replace('.avi', '_final.mp4')
        cmd = [
            'ffmpeg',
            '-y',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-strict', 'experimental',
            output_path
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f'รวมไฟล์สำเร็จ: {output_path}')
            self.update_info(f'รวมไฟล์เสียงและวิดีโอเสร็จสิ้น:\n{output_path}')
        except Exception as e:
            print('รวมไฟล์เสียง-วิดีโอล้มเหลว:', e)
            self.update_info('รวมไฟล์เสียง-วิดีโอผิดพลาด')

    @mainthread
    def update_info(self, text):
        self.ids.info_label.text = text


class GalleryScreen(Screen):
    def on_enter(self):
        self.load_gallery()

    def load_gallery(self):
        grid = self.ids.gallery_grid
        grid.clear_widgets()
        files = sorted(os.listdir(PHOTO_DIR), reverse=True)
        for f in files:
            if not f.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            path = os.path.join(PHOTO_DIR, f)
            caption = f"{f}\n{time.ctime(os.path.getmtime(path))}"
            img = AsyncImage(source=path, size_hint_y=None, height=180)
            layout = BoxLayout(orientation='vertical', size_hint_y=None, height=260, padding=5, spacing=5)
            layout.add_widget(img)
            label = Label(text=caption, size_hint_y=None, height=40, halign='center', valign='middle',font_name='THSarabun')
            label.text_size = label.size
            layout.add_widget(label)

            btn_del = Button(text='ลบ', size_hint_y=None, height=40,font_name='THSarabun')
            btn_del.bind(on_release=lambda inst, p=path: self.confirm_delete(p))
            layout.add_widget(btn_del)

            grid.add_widget(layout)

    def confirm_delete(self, path):
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(text='ต้องการลบภาพนี้หรือไม่?',font_name='THSarabun'))
        btns = BoxLayout(spacing=10, size_hint_y=None, height=40)
        btn_yes = Button(text='ใช่',font_name='THSarabun')
        btn_no = Button(text='ไม่',font_name='THSarabun')
        btns.add_widget(btn_yes)
        btns.add_widget(btn_no)
        content.add_widget(btns)
        popup = Popup(title='ยืนยันการลบ', content=content, size_hint=(.6, .4),font_name='THSarabun')
        btn_yes.bind(on_release=lambda x: self.delete_image(path, popup))
        btn_no.bind(on_release=popup.dismiss)
        popup.open()

    def delete_image(self, path, popup):
        try:
            os.remove(path)
            self.load_gallery()
            popup.dismiss()
        except Exception as e:
            print('ลบภาพผิดพลาด:', e)
            popup.dismiss()

    def confirm_delete_all(self):
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(text='ต้องการลบภาพทั้งหมดหรือไม่?'),font_name='THSarabun')
        btns = BoxLayout(spacing=10, size_hint_y=None, height=40)
        btn_yes = Button(text='ใช่',font_name='THSarabun')
        btn_no = Button(text='ไม่',font_name='THSarabun')
        btns.add_widget(btn_yes)
        btns.add_widget(btn_no)
        content.add_widget(btns)
        popup = Popup(title='ยืนยันการลบทั้งหมด', content=content, size_hint=(.6, .4),font_name='THSarabun')
        btn_yes.bind(on_release=lambda x: self.delete_all_images(popup))
        btn_no.bind(on_release=popup.dismiss)
        popup.open()

    def delete_all_images(self, popup):
        try:
            for f in os.listdir(PHOTO_DIR):
                if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                    os.remove(os.path.join(PHOTO_DIR, f))
            self.load_gallery()
            popup.dismiss()
        except Exception as e:
            print('ลบภาพทั้งหมดผิดพลาด:', e)
            popup.dismiss()


class CameraApp(App):
    def build(self):
        Builder.load_file('camera.kv')
        sm = ScreenManager()
        sm.add_widget(CameraSelectScreen(name='select'))
        sm.add_widget(LiveScreen(name='live'))
        sm.add_widget(GalleryScreen(name='gallery'))
        sm.current = 'select'
        return sm


if __name__ == '__main__':
    CameraApp().run()
