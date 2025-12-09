# rpi_camera_controller_opencv/services/facebook_service.py

import requests
from ..config import FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID

class FacebookService:
    def __init__(self):
        self.access_token = FACEBOOK_ACCESS_TOKEN
        self.page_id = FACEBOOK_PAGE_ID
        self.graph_url = "https://graph.facebook.com/v19.0/"

    def share_media(self, media_url: str, caption: str = "Captured from Raspberry Pi Camera") -> dict:
        """
        Shares an image or video (hosted on a public URL like S3) to Facebook.
        
        :param media_url: Public URL of the image or video (e.g., S3 URL).
        :param caption: Text caption for the post.
        :return: Dictionary with success status and post ID or error message.
        """
        if self.access_token == "YOUR_FACEBOOK_ACCESS_TOKEN":
            return {'success': False, 'error': 'Facebook Access Token not configured in config.py.'}

        # Determine if it's an image or video based on URL extension (simple check)
        is_video = media_url.lower().endswith(('.mp4', '.mov', '.avi', '.h264'))
        
        if is_video:
            endpoint = f"{self.page_id or 'me'}/videos"
            data = {
                'file_url': media_url,
                'description': caption,
                'access_token': self.access_token
            }
        else:
            endpoint = f"{self.page_id or 'me'}/photos"
            data = {
                'url': media_url,
                'caption': caption,
                'access_token': self.access_token
            }

        try:
            url = self.graph_url + endpoint
            response = requests.post(url, data=data)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            
            result = response.json()
            if 'id' in result:
                return {'success': True, 'post_id': result['id'], 'message': 'Successfully shared to Facebook.'}
            elif 'error' in result:
                return {'success': False, 'error': result['error']['message']}
            else:
                return {'success': False, 'error': 'Unknown response from Facebook API.'}

        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f"Facebook API Request Error: {e}"}
        except Exception as e:
            return {'success': False, 'error': f"Unexpected Error: {e}"}

# Example Usage (for testing purposes)
if __name__ == '__main__':
    fb_service = FacebookService()
    
    # Simulate sharing a public S3 image URL
    test_image_url = "https://your-rpi-camera-bucket-name.s3.ap-southeast-1.amazonaws.com/test_image.jpg"
    print(f"Simulating sharing image: {test_image_url}")
    # result = fb_service.share_media(test_image_url, caption="Test post from RPi!")
    # print(f"Share Result: {result}")
    
    # Simulate sharing a public S3 video URL
    test_video_url = "https://your-rpi-camera-bucket-name.s3.ap-southeast-1.amazonaws.com/test_video.mp4"
    print(f"Simulating sharing video: {test_video_url}")
    # result = fb_service.share_media(test_video_url, caption="Test video post from RPi!")
    # print(f"Share Result: {result}")
