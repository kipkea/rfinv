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
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty
from kivy.logger import Logger
from kivy.core.text import LabelBase

# กำหนด Global Font สำหรับภาษาไทย
LabelBase.register(name='NotoSansThai', fn_regular='fonts/NotoSansThai-Regular.ttf')

# Add project root to path for module imports
sys.path.append(os.path.dirname(__file__))

from services.camera_service import CameraService
from services.network_service import NetworkService

# --- Kivy UI Classes (Popups) ---

class TaggingPopup(Popup):
    font_name = 'NotoSansThai'
    """Popup for user to input filename and tags before capture/upload."""
    """Popup for user to input filename and tags before capture/upload."""
    capture_type = StringProperty('')
    main_screen = ObjectProperty(None)

    def save_and_upload(self, user_filename, user_tags):
        self.dismiss()
        self.main_screen.handle_capture_and_save(
            self.capture_type, 
            user_filename, 
            user_tags
        )

class ImageProcessingPopup(Popup):
    font_name = 'NotoSansThai'
    """Popup for real-time image processing settings."""
    """Popup for real-time image processing settings."""
    main_screen = ObjectProperty(None)
    
    def on_open(self):
        # Load current settings into the UI elements
        params = self.main_screen.camera_service.processing_params
        self.ids.brightness_slider.value = params['brightness']
        self.ids.contrast_slider.value = params['contrast']
        self.ids.sharpness_slider.value = params['sharpness']
        self.ids.resize_slider.value = params['resize_factor']
        self.ids.color_mode_btn.text = params['color_mode']
        self.ids.filter_btn.text = params['filter']
        
    def set_param(self, key, value):
        self.main_screen.camera_service.set_processing_param(key, value)
        
    def set_color_mode(self, mode):
        self.ids.color_mode_btn.text = mode
        self.set_param('color_mode', mode)
        
    def set_filter(self, filter_type):
        self.ids.filter_btn.text = filter_type
        self.set_param('filter', filter_type)

class SettingsPopup(Popup):
    font_name = 'NotoSansThai'
    main_screen = ObjectProperty(None)
    # ลบการอ้างอิง AWS ออกจาก SettingsPopup
    def on_open(self):
        # Load current settings into the text inputs
        # Note: Network settings are not loaded from config, as they are dynamic
        pass

    def save_settings(self, *args):
        # No AWS settings to save in this version
        self.main_screen.update_status("การตั้งค่าถูกบันทึกแล้ว (เฉพาะ Network)")
        self.dismiss()

    def connect_wifi(self, ssid, password):
        net_service = NetworkService()
        result = net_service.set_wifi_connection(ssid, password)
        self.main_screen.update_status(result['message'])
        # In a real app, you might want to keep the popup open to show status

class HistoryPopup(Popup):
    # ลบ HistoryPopup ออกเพราะไม่มี AWS S3
    pass
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



# --- Main Screen Class ---

class MainScreen(BoxLayout):
    font_name = 'NotoSansThai'
    """The main single-screen UI for the camera controller."""
    
    is_recording = BooleanProperty(False)
    last_capture_path = StringProperty('')
    is_barcode_detection_enabled = BooleanProperty(False)
    barcode_result_text = StringProperty('สถานะ Barcode/QR: ปิด')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera_service = CameraService()
        # self.aws_service = AWSService()
        # self.facebook_service = FacebookService()
        
        # Initialize camera and start the clock for live preview
        if self.camera_service.initialize_camera():
            Clock.schedule_interval(self.update_preview, 1.0 / 30.0) # 30 FPS update
        else:
            self.update_status("ERROR: ไม่สามารถเปิดกล้องได้ โปรดตรวจสอบการเชื่อมต่อและ config")

    def update_preview(self, dt):
        """Reads a processed frame from CameraService and updates the Kivy Image widget."""
        frame, barcode_results = self.camera_service.get_processed_frame()
        
        if frame is not None:
            # Convert OpenCV BGR frame to Kivy Texture
            # Note: We flip the frame vertically (0) for correct display in Kivy
            buf = cv2.flip(frame, 0).tobytes()
            image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            
            # Update the Image widget
            self.ids.camera_preview.texture = image_texture
            
            # Update Barcode/QR Status
            if self.is_barcode_detection_enabled:
                if barcode_results:
                    first_result = barcode_results[0]
                    self.barcode_result_text = f"✅ {first_result['type']}: {first_result['data'][:30]}..."
                else:
                    self.barcode_result_text = "❌ ไม่พบ Barcode/QR"
            else:
                self.barcode_result_text = "สถานะ Barcode/QR: ปิด"
            
            # Update Status Bar with Barcode Info
            self.ids.status_bar.text = f"สถานะ: {'🔴 บันทึก' if self.is_recording else 'พร้อมใช้งาน'} | {self.barcode_result_text}"
            
            # If recording, write the frame (CameraService handles getting the processed frame)
            if self.is_recording:
                self.camera_service.record_frame()

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
                self.ids.status_bar.text = f"🔴 บันทึกวิดีโอ... | {self.barcode_result_text}"
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
                self.ids.status_bar.text = f"✅ หยุดบันทึกแล้ว | {self.barcode_result_text}"
                self.update_status(f"หยุดบันทึกแล้ว: {os.path.basename(stopped_path)}. กำลังรออัปโหลด...")
                
                # Automatically show tagging popup for video upload
                self.show_tagging_popup('video')
            else:
                self.update_status("ERROR: ไม่สามารถหยุดบันทึกได้")

    def handle_capture_and_save(self, capture_type, user_filename, user_tags):
        """Handles the actual capture/saving and S3 upload."""
        
        if capture_type == 'image':
            # 1. Capture Image
            local_path = self.camera_service.capture_image(user_filename, user_tags)
        elif capture_type == 'video':
            # 1. Use the path from the stopped recording
            local_path = self.last_capture_path
            # Note: Video recording already includes user_filename and user_tags in the filename
        else:
            self.update_status("ERROR: ประเภทการจับภาพไม่ถูกต้อง")
            return

        if not local_path:
            self.update_status("ERROR: ไม่สามารถบันทึกไฟล์ได้")
            return

        self.last_capture_path = local_path
        self.ids.share_btn.disabled = True # No sharing in this version
        self.update_status(f"บันทึกไฟล์สำเร็จ: {os.path.basename(local_path)}")

    def share_last_capture(self):
        """Placeholder for sharing functionality (disabled in local version)."""
        self.update_status("ฟังก์ชันแชร์ถูกปิดใช้งานในเวอร์ชัน Local Storage")

    def show_settings_popup(self):
        """Shows the network settings popup."""
        popup = SettingsPopup(main_screen=self)
        popup.open()
        
    def show_image_processing_popup(self):
        """Shows the image processing settings popup."""
        popup = ImageProcessingPopup(main_screen=self)
        popup.open()

    def toggle_barcode_detection(self):
        """Toggles the barcode detection feature."""
        self.is_barcode_detection_enabled = not self.is_barcode_detection_enabled
        self.camera_service.toggle_barcode_detection(self.is_barcode_detection_enabled)
        
        if self.is_barcode_detection_enabled:
            self.ids.barcode_btn.text = '🔍 Barcode: ON'
            self.barcode_result_text = "สถานะ Barcode/QR: กำลังค้นหา..."
        else:
            self.ids.barcode_btn.text = '🔍 Barcode: OFF'
            self.barcode_result_text = "สถานะ Barcode/QR: ปิด"
        
        Logger.info(f"MainScreen: Barcode detection toggled to {self.is_barcode_detection_enabled}")

    def show_history_popup(self):
        """Placeholder for history functionality (disabled in local version)."""
        self.update_status("ฟังก์ชันประวัติถูกปิดใช้งานในเวอร์ชัน Local Storage")
        
    def on_stop(self):
        """Release camera when the app stops."""
        self.camera_service.release_camera()

# --- Kivy App Entry Point ---

class RPiCameraControllerApp(App):
    def build(self):
        # Load the KV file
        Builder.load_file('./kv/main_ui.kv')
        return MainScreen()

if __name__ == '__main__':
    # No need to create TEMP_DIR, CameraService handles OUTPUT_DIR
    RPiCameraControllerApp().run()
