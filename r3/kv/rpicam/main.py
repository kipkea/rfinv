# rpi_camera_controller_opencv/main.py

import os
import sys
import cv2
import numpy as np
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.image import Image as KivyImage
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty

# Add project root to path for module imports
sys.path.append(os.path.dirname(__file__))

from services.camera_service import CameraService
from services.aws_service import AWSService
from services.network_service import NetworkService
from services.facebook_service import FacebookService
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME, FACEBOOK_ACCESS_TOKEN

# --- Kivy UI Classes (Popups) ---

class TaggingPopup(Popup):
    """Popup for user to input filename and tags before capture/upload."""
    capture_type = StringProperty('')
    main_screen = ObjectProperty(None)

    def save_and_upload(self, user_filename, user_tags):
        self.dismiss()
        self.main_screen.handle_capture_and_upload(
            self.capture_type, 
            user_filename, 
            user_tags
        )

class SettingsPopup(Popup):
    """Popup for configuring AWS and Network settings."""
    main_screen = ObjectProperty(None)

    def on_open(self):
        # Load current settings into the text inputs
        self.ids.aws_key_id.text = AWS_ACCESS_KEY_ID
        self.ids.aws_secret_key.text = AWS_SECRET_ACCESS_KEY
        self.ids.aws_bucket_name.text = S3_BUCKET_NAME
        # Note: Network settings are not loaded from config, as they are dynamic

    def save_settings(self, key_id, secret_key, bucket_name):
        # In a real app, you would save these to a persistent config file
        # For this example, we just update the config module variables (temporary)
        # and re-initialize the AWS service.
        # NOTE: This is a simplified approach. Proper config management is needed.
        
        # Update config variables (simulated persistence)
        # from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME
        # AWS_ACCESS_KEY_ID = key_id
        # AWS_SECRET_ACCESS_KEY = secret_key
        # S3_BUCKET_NAME = bucket_name
        
        self.main_screen.update_status("การตั้งค่า AWS ถูกบันทึกแล้ว (ต้องรีสตาร์ทแอปเพื่อโหลดเต็มรูปแบบ)")
        self.dismiss()

    def connect_wifi(self, ssid, password):
        net_service = NetworkService()
        result = net_service.set_wifi_connection(ssid, password)
        self.main_screen.update_status(result['message'])
        # In a real app, you might want to keep the popup open to show status

class HistoryPopup(Popup):
    """Popup for viewing S3 upload history."""
    main_screen = ObjectProperty(None)

    def on_open(self):
        self.main_screen.update_status("กำลังโหลดประวัติจาก AWS S3...")
        self.load_history()

    def load_history(self):
        aws_service = AWSService()
        history_data = aws_service.get_history(max_keys=10)
        
        history_list = self.ids.history_list
        history_list.clear_widgets()
        
        if not history_data:
            history_list.add_widget(Label(text="ไม่พบประวัติการอัปโหลด", size_hint_y=None, height=40))
            self.main_screen.update_status("โหลดประวัติเสร็จสิ้น")
            return

        for item in history_data:
            box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)
            box.add_widget(Label(text=item['filename'], size_hint_x=0.5, font_size=14))
            box.add_widget(Label(text=f"{item['last_modified'][:10]}", size_hint_x=0.2, font_size=14))
            box.add_widget(Button(text="ดู/แชร์", size_hint_x=0.3, font_size=14, 
                                  on_release=lambda btn, url=item['url']: self.main_screen.handle_history_share(url)))
            history_list.add_widget(box)
            
        history_list.height = len(history_data) * 45 # Adjust height for ScrollView
        self.main_screen.update_status(f"โหลดประวัติ {len(history_data)} รายการเสร็จสิ้น")

# --- Main Screen Class ---

class MainScreen(BoxLayout):
    """The main single-screen UI for the camera controller."""
    
    is_recording = BooleanProperty(False)
    last_capture_path = StringProperty('')
    last_capture_url = StringProperty('')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera_service = CameraService()
        self.aws_service = AWSService()
        self.facebook_service = FacebookService()
        
        # Initialize camera and start the clock for live preview
        if self.camera_service.initialize_camera():
            Clock.schedule_interval(self.update_preview, 1.0 / 30.0) # 30 FPS update
        else:
            self.update_status("ERROR: ไม่สามารถเปิดกล้องได้ โปรดตรวจสอบการเชื่อมต่อและ config")

    def update_preview(self, dt):
        """Reads a frame from OpenCV and updates the Kivy Image widget."""
        frame = self.camera_service.get_frame()
        
        if frame is not None:
            # Convert OpenCV BGR frame to Kivy Texture
            buf = cv2.flip(frame, 0).tobytes()
            image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            
            # Update the Image widget
            self.ids.camera_preview.texture = image_texture
            
            # If recording, write the frame
            if self.is_recording:
                self.camera_service.record_frame(frame)

    def update_status(self, message):
        """Updates the status bar with a message."""
        self.ids.status_bar.text = f"สถานะ: {message}"

    # --- Control Panel Functions ---

    def show_tagging_popup(self, capture_type):
        """Shows the popup to get user input for filename and tags."""
        popup = TaggingPopup(capture_type=capture_type, main_screen=self)
        popup.open()

    def toggle_recording(self):
        """Starts or stops video recording."""
        if not self.is_recording:
            # Start recording
            video_path = self.camera_service.start_recording()
            if video_path:
                self.is_recording = True
                self.ids.record_btn.text = '⏹️ หยุดบันทึก'
                self.update_status(f"เริ่มบันทึกวิดีโอ: {os.path.basename(video_path)}")
            else:
                self.update_status("ERROR: ไม่สามารถเริ่มบันทึกได้")
        else:
            # Stop recording
            stopped_path = self.camera_service.stop_recording()
            if stopped_path:
                self.is_recording = False
                self.ids.record_btn.text = '🔴 บันทึก'
                self.last_capture_path = stopped_path
                self.update_status(f"หยุดบันทึกแล้ว: {os.path.basename(stopped_path)}. กำลังรออัปโหลด...")
                
                # Automatically show tagging popup for video upload
                self.show_tagging_popup('video')
            else:
                self.update_status("ERROR: ไม่สามารถหยุดบันทึกได้")

    def handle_capture_and_upload(self, capture_type, user_filename, user_tags):
        """Handles the actual capture/saving and S3 upload."""
        
        if capture_type == 'image':
            # 1. Capture Image
            local_path = self.camera_service.capture_image(user_filename)
            content_type = 'image/jpeg'
        elif capture_type == 'video':
            # 1. Use the path from the stopped recording
            local_path = self.last_capture_path
            content_type = 'video/x-msvideo' # Use AVI/XVID type for now, conversion needed for mp4
        else:
            self.update_status("ERROR: ประเภทการจับภาพไม่ถูกต้อง")
            return

        if not local_path:
            self.update_status("ERROR: ไม่สามารถบันทึกไฟล์ได้")
            return

        self.update_status(f"กำลังอัปโหลด {os.path.basename(local_path)} ไปยัง AWS S3...")
        
        # 2. Upload to S3
        upload_result = self.aws_service.upload_file(local_path, user_tags, content_type)
        
        if upload_result['success']:
            self.last_capture_url = upload_result['url']
            self.ids.share_btn.disabled = False
            self.update_status(f"อัปโหลดสำเร็จ! URL: {self.last_capture_url}")
            
            # 3. Clean up local file
            os.remove(local_path)
        else:
            self.update_status(f"ERROR: อัปโหลดล้มเหลว: {upload_result['error']}")

    def share_last_capture(self):
        """Shares the last uploaded media to Facebook."""
        if not self.last_capture_url:
            self.update_status("ERROR: ไม่มีไฟล์ที่อัปโหลดล่าสุดให้แชร์")
            return

        self.update_status("กำลังแชร์ไป Facebook...")
        
        # Use user-defined caption or a default one
        caption = f"ภาพ/วิดีโอใหม่จากกล้อง Raspberry Pi! URL: {self.last_capture_url}"
        
        share_result = self.facebook_service.share_media(self.last_capture_url, caption)
        
        if share_result['success']:
            self.update_status(f"แชร์สำเร็จ! Post ID: {share_result['post_id']}")
        else:
            self.update_status(f"ERROR: แชร์ล้มเหลว: {share_result['error']}")

    def show_settings_popup(self):
        """Shows the settings popup."""
        popup = SettingsPopup(main_screen=self)
        popup.open()

    def show_history_popup(self):
        """Shows the history popup."""
        popup = HistoryPopup(main_screen=self)
        popup.open()

    def handle_history_share(self, url):
        """Handles sharing a file selected from the history."""
        self.last_capture_url = url
        self.share_last_capture()
        
    def on_stop(self):
        """Release camera when the app stops."""
        self.camera_service.release_camera()

# --- Kivy App Entry Point ---

class RPiCameraControllerApp(App):
    def build(self):
        # Load the KV file
        Builder.load_file('rpi_camera_controller_opencv/kv/main_ui.kv')
        return MainScreen()

if __name__ == '__main__':
    # Create temp directory if it doesn't exist
    os.makedirs(TEMP_DIR, exist_ok=True)
    RPiCameraControllerApp().run()
