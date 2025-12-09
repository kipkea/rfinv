'''
# rpi_camera_controller_opencv/config.py

# AWS S3 Configuration
# **WARNING**: For production, use IAM Roles or Secrets Manager instead of storing keys directly.
AWS_ACCESS_KEY_ID = "YOUR_AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY = "YOUR_AWS_SECRET_ACCESS_KEY"
AWS_REGION_NAME = "ap-southeast-1"  # e.g., 'ap-southeast-1' (Singapore)
S3_BUCKET_NAME = "your-rpi-camera-bucket-name"

# Facebook API Configuration
# Requires a Long-Lived User Access Token or Page Access Token
FACEBOOK_ACCESS_TOKEN = "YOUR_FACEBOOK_ACCESS_TOKEN"
FACEBOOK_PAGE_ID = "YOUR_FACEBOOK_PAGE_ID" # Optional: If sharing to a specific page

# Application Settings
PREVIEW_WIDTH = 640
PREVIEW_HEIGHT = 480
FRAME_RATE = 30

# File Paths
TEMP_DIR = "./rpi_camera_temp"
IMAGE_FORMAT = "jpg"
VIDEO_FORMAT = "h264" # Picamera2 default, will need conversion to mp4 for sharing
'''



# AWS S3 Configuration
# **WARNING**: For production, use IAM Roles or Secrets Manager instead of storing keys directly.
#AWS_ACCESS_KEY_ID = "YOUR_AWS_ACCESS_KEY_ID"
#AWS_SECRET_ACCESS_KEY = "YOUR_AWS_SECRET_ACCESS_KEY"
#AWS_REGION_NAME = "ap-southeast-1"  # e.g., 'ap-southeast-1' (Singapore)
#S3_BUCKET_NAME = "your-rpi-camera-bucket-name"

# Facebook API Configuration
# Requires a Long-Lived User Access Token or Page Access Token
#FACEBOOK_ACCESS_TOKEN = "YOUR_FACEBOOK_ACCESS_TOKEN"
#FACEBOOK_PAGE_ID = "YOUR_FACEBOOK_PAGE_ID" # Optional: If sharing to a specific page

# Application Settings
PREVIEW_WIDTH = 640
PREVIEW_HEIGHT = 480
FRAME_RATE = 30

# File Paths
TEMP_DIR = "./rpi_camera_temp"
IMAGE_FORMAT = "jpg"
VIDEO_FORMAT = "h264" # Picamera2 default, will need conversion to mp4 for sharing