# rpi_camera_controller_opencv/services/camera_service.py

import cv2
import os
import time
import uuid
import re
from datetime import datetime
import numpy as np
from config import PREVIEW_WIDTH, PREVIEW_HEIGHT, IMAGE_FORMAT, VIDEO_FORMAT
import math
# กำหนดโฟลเดอร์สำหรับเก็บไฟล์ภาพ/วิดีโอ
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")

class CameraService:
    def __init__(self):
        self.cap = None
        self.is_recording = False
        self.video_writer = None
        self.video_file_path = None # เพิ่มตัวแปรสำหรับเก็บชื่อไฟล์วิดีโอ
        self.output_dir = OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Image Processing Parameters
        self.processing_params = {
            'brightness': 1.0,  # Multiplier (0.0 to 2.0)
            'contrast': 1.0,    # Multiplier (0.0 to 2.0)
            'sharpness': 0,     # 0=None, 1=Mild, 2=Strong (Simulated)
            'color_mode': 'BGR', # 'BGR', 'GRAY', 'HSV'
            'filter': 'None',   # 'None', 'Sobel', 'Canny'
            'resize_factor': 1.0 # Multiplier (0.5 to 2.0)
        }

    def initialize_camera(self, camera_index=0):
        """
        Initializes the camera using OpenCV's VideoCapture.
        
        :param camera_index: Index of the camera (usually 0).
        :return: True if successful, False otherwise.
        """
        if self.cap and self.cap.isOpened():
            self.cap.release()
            
        # Try to open the camera
        # NOTE: On RPi 5 Bookworm, this might require specific GStreamer backends or a USB camera.
        # For CSI camera, the user might need to configure GStreamer or use Picamera2/libcamera
        self.cap = cv2.VideoCapture(camera_index)
        
        if not self.cap.isOpened():
            print(f"Error: Could not open camera index {camera_index}. Check camera connection and V4L2/GStreamer configuration.")
            return False

        # Set properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, PREVIEW_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, PREVIEW_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        print(f"Camera initialized: {self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)} @ {self.cap.get(cv2.CAP_PROP_FPS)} FPS")
        return True

    def get_raw_frame(self) -> np.ndarray or None:
        """
        Reads a single raw frame from the camera.
        
        :return: A numpy array representing the frame (BGR format) or None.
        """
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None
        
    def set_processing_param(self, key: str, value):
        """Sets a single image processing parameter."""
        if key in self.processing_params:
            self.processing_params[key] = value
            print(f"Processing param updated: {key} = {value}")
            
    def get_processed_frame(self) -> np.ndarray or None:
        """
        Reads a raw frame and applies the image processing pipeline.
        
        :return: A numpy array representing the processed frame or None.
        """
        frame = self.get_raw_frame()
        if frame is None:
            return None
            
        # 1. Resize (if factor is not 1.0)
        factor = self.processing_params['resize_factor']
        if factor != 1.0:
            new_width = int(frame.shape[1] * factor)
            new_height = int(frame.shape[0] * factor)
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            
        # 2. Brightness and Contrast (Linear transformation: g(x) = alpha * f(x) + beta)
        alpha = self.processing_params['contrast'] # Contrast control (1.0-3.0)
        beta = (self.processing_params['brightness'] - 1.0) * 100 # Brightness control (-100 to 100)
        frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
        
        # 3. Sharpness (Simulated with a simple kernel or Laplacian)
        sharpness_level = self.processing_params['sharpness']
        if sharpness_level > 0:
            # Simple unsharp mask simulation
            kernel_size = 5
            sigma = 1.0 + sharpness_level * 0.5
            blurred = cv2.GaussianBlur(frame, (kernel_size, kernel_size), sigma)
            frame = cv2.addWeighted(frame, 1.5, blurred, -0.5, 0)
            
        # 4. Color Mode Conversion
        color_mode = self.processing_params['color_mode']
        if color_mode == 'GRAY':
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR) # Convert back to BGR for Kivy display
        elif color_mode == 'HSV':
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            frame = cv2.cvtColor(frame, cv2.COLOR_HSV2BGR) # Convert back to BGR for Kivy display
            
        # 5. Filter Application (Edge Detection)
        filter_type = self.processing_params['filter']
        if filter_type != 'None':
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if filter_type == 'Sobel':
                sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=5)
                sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)
                abs_sobelx = cv2.convertScaleAbs(sobelx)
                abs_sobely = cv2.convertScaleAbs(sobely)
                frame = cv2.addWeighted(abs_sobelx, 0.5, abs_sobely, 0.5, 0)
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR) # Convert back to BGR
            elif filter_type == 'Canny':
                frame = cv2.Canny(gray, 100, 200)
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR) # Convert back to BGR
                
        return frame

    def capture_image(self, user_filename: str = None, user_tags: str = None) -> str or None:
        """
        Captures a single image and saves it to the temporary directory.
        
        :param user_filename: Optional filename provided by the user (without extension).
        :return: Absolute path to the saved image file or None on failure.
        """
        # Use the processed frame for capture
        frame = self.get_processed_frame()
        if frame is None:
            print("Error: Cannot capture image, no frame available.")
            return None

        # Convert BGR to RGB for better compatibility (though saving as BGR is fine for cv2)
        # frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Generate unique filename
        filename = self._generate_unique_filename(user_filename, user_tags, IMAGE_FORMAT)
        file_path = os.path.join(self.output_dir, filename)
        
        # Save the image
        if cv2.imwrite(file_path, frame):
            print(f"Image saved to: {file_path}")
            return file_path
        else:
            print(f"Error: Failed to save image to {file_path}")
            return None

    def start_recording(self, user_filename: str = None) -> str or None:
        """
        Starts video recording.
        
        :param user_filename: Optional filename provided by the user (without extension).
        :return: Absolute path to the video file being recorded or None on failure.
        """
        if self.is_recording:
            return None

        # Use the processed frame for capture
        frame = self.get_processed_frame()
        if frame is None:
            print("Error: Cannot start recording, no frame available.")
            return None

        # Generate unique filename
        filename = self._generate_unique_filename(user_filename, None, 'avi') # Use AVI for raw capture
        file_path = os.path.join(self.output_dir, filename)
        
        # Define the codec and create VideoWriter object
        # Use XVID or MJPG for better compatibility on RPi
        fourcc = cv2.VideoWriter_fourcc(*'XVID') 
        fps = self.cap.get(cv2.CAP_PROP_FPS) if self.cap.get(cv2.CAP_PROP_FPS) > 0 else 20.0
        
        self.video_writer = cv2.VideoWriter(
            file_path, 
            fourcc, 
            fps, 
            (frame.shape[1], frame.shape[0])
        )
        self.video_file_path = file_path # เก็บชื่อไฟล์ไว้ใน instance variable
        
        if not self.video_writer.isOpened():
            print(f"Error: Could not create VideoWriter for {file_path}")
            return None

        self.is_recording = True
        print(f"Recording started to: {file_path}")
        return file_path

    def record_frame(self):
        """Writes the current processed frame to the video file if recording is active."""
        if self.is_recording and self.video_writer:
            frame = self.get_processed_frame()
            if frame is not None:
                self.video_writer.write(frame)

    def stop_recording(self) -> str or None:
        """
        Stops video recording and releases the VideoWriter.
        
        :return: Absolute path to the saved video file or None if not recording.
        """
        if not self.is_recording:
            return None

        file_path = self.video_file_path # ใช้ตัวแปรที่เก็บไว้แทน getFilename()
        self.video_writer.release()
        self.is_recording = False
        self.video_writer = None
        self.video_file_path = None # ล้างค่าเมื่อหยุดบันทึก
        
        print(f"Recording stopped. File saved to: {file_path}")
        
        # NOTE: For Facebook sharing, the file might need to be converted to MP4/H.264
        # This conversion step is omitted here but should be done before S3 upload/sharing.
        
        return file_path

    def release_camera(self):
        """Releases the camera resource."""
        if self.cap:
            self.cap.release()
            self.cap = None
            print("Camera released.")

    def _generate_unique_filename(self, user_filename: str or None, user_tags: str or None, extension: str) -> str:
        """Generates a unique filename based on timestamp and optional user input."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        # Clean and format tags
        tags_str = "_".join([tag.strip() for tag in (user_tags or "").split(',') if tag.strip()])
        
        # Base name construction
        if user_filename:
            # Sanitize user input and combine with unique ID
            sanitized_name = re.sub(r'[^\w\-]', '', user_filename).strip()
            base_name = f"{sanitized_name}_{timestamp}_{unique_id}" if sanitized_name else f"capture_{timestamp}_{unique_id}"
        else:
            base_name = f"capture_{timestamp}_{unique_id}"
            
        # Append tags if available
        if tags_str:
            base_name = f"{base_name}_{tags_str}"
            
        return f"{base_name}.{extension}"

# Example Usage (for testing purposes)
if __name__ == '__main__':
    cam_service = CameraService()
    if cam_service.initialize_camera():
        # Test image capture
        image_path = cam_service.capture_image("My_Test_Photo")
        print(f"Captured Image Path: {image_path}")
        
        # Test video recording (simulated short loop)
        video_path = cam_service.start_recording("My_Test_Video")
        if video_path:
            for _ in range(30): # Record for 1 second at 30 FPS
                frame = cam_service.get_frame()
                if frame is not None:
                    cam_service.record_frame(frame)
                time.sleep(1/30)
            stopped_path = cam_service.stop_recording()
            print(f"Stopped Video Path: {stopped_path}")
            
        cam_service.release_camera()
