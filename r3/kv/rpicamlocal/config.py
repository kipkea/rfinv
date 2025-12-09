
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

