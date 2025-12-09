
# rpi_camera_controller_opencv/config.py

# Configuration for Local Storage Version

# Application Settings
PREVIEW_WIDTH = 640
PREVIEW_HEIGHT = 480
FRAME_RATE = 30

# File Paths
# TEMP_DIR is no longer needed as files are saved directly to the 'images' folder
IMAGE_FORMAT = "jpg"
VIDEO_FORMAT = "h264" # Picamera2 default, will need conversion to mp4 for sharing
IMAGE_SAVE_PATH = "images/"
VIDEO_SAVE_PATH = "videos/" 
# Ensure the directories exist
import os
os.makedirs(IMAGE_SAVE_PATH, exist_ok=True)
os.makedirs(VIDEO_SAVE_PATH, exist_ok=True)         
# Camera Settings
CAMERA_RESOLUTION = (1920, 1080)
CAMERA_FRAMERATE = 30
CAMERA_BRIGHTNESS = 50  # Range: 0-100
CAMERA_CONTRAST = 0     # Range: -100 to 100
CAMERA_SATURATION = 0   # Range: -100 to 100
CAMERA_ISO = 100        # Range: 100-800        
CAMERA_SHUTTER_SPEED = 0  # Auto (0) or specify in microseconds
CAMERA_AWB_MODE = "auto"  # Options: 'auto', 'sunlight', 'cloudy', etc.
CAMERA_EXPOSURE_MODE = "auto"  # Options: 'auto', 'night
# Other Settings
BARCODE_DETECTION_ENABLED = True
BARCODE_TYPES = ["qrcode", "code128", "ean13"]  # Supported barcode types
LOG_LEVEL = "DEBUG"  # Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR' 
MAX_VIDEO_DURATION = 600  # Maximum video duration in seconds
MAX_IMAGE_COUNT = 1000  # Maximum number of images to store
IMAGE_COMPRESSION_QUALITY = 85  # JPEG quality (1-100)
VIDEO_CONVERSION_ENABLED = True  # Convert h264 to mp4 after recording
VIDEO_MP4_BITRATE = "5000k"  # Bitrate for mp4 conversion
FFMPEG_PATH = "ffmpeg"  # Path to ffmpeg executable
# Network Settings (if applicable)
WIFI_SSID = "YourSSID"
WIFI_PASSWORD = "YourPassword"
FTP_UPLOAD_ENABLED = False
FTP_SERVER = "ftp.yourserver.com"
FTP_USERNAME = "username"
FTP_PASSWORD = "password"
FTP_UPLOAD_PATH = "/uploads/"
FTP_UPLOAD_INTERVAL = 300  # Upload interval in seconds
# Cloud Integration Settings (if applicable)
CLOUD_SYNC_ENABLED = False
CLOUD_API_KEY = "your_api_key"
CLOUD_UPLOAD_PATH = "/cloud/uploads/"   
CLOUD_SYNC_INTERVAL = 600  # Sync interval in seconds   
# Notification Settings
NOTIFICATIONS_ENABLED = True
EMAIL_NOTIFICATIONS_ENABLED = False
EMAIL_SMTP_SERVER = "smtp.yourserver.com"
EMAIL_SMTP_PORT = 587
EMAIL_USERNAME = "mail"
EMAIL_PASSWORD = "password" 
EMAIL_RECIPIENT = "" 


