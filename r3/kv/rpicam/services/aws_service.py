# rpi_camera_controller_opencv/services/aws_service.py

import boto3
import os
from botocore.exceptions import ClientError
from ..config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION_NAME, S3_BUCKET_NAME

class AWSService:
    def __init__(self):
        """Initializes the Boto3 S3 client."""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION_NAME
            )
            self.bucket_name = S3_BUCKET_NAME
        except Exception as e:
            print(f"Error initializing Boto3 client: {e}")
            self.s3_client = None

    def upload_file(self, file_path: str, tags: str = "", content_type: str = 'image/jpeg') -> dict:
        """
        Uploads a file to the configured S3 bucket.
        
        :param file_path: Local path to the file to upload.
        :param tags: User-defined tags to be stored as S3 metadata.
        :param content_type: MIME type of the file (e.g., 'image/jpeg', 'video/mp4').
        :return: Dictionary with success status and URL or error message.
        """
        if not self.s3_client:
            return {'success': False, 'error': 'AWS client not initialized.'}

        object_name = os.path.basename(file_path)
        
        # Prepare metadata for tagging and tracking
        metadata = {
            'user-tags': tags.replace(' ', '_'), # S3 metadata keys are case-insensitive and should be simple
            'original-filename': object_name,
            'content-type': content_type
        }

        extra_args = {
            'ContentType': content_type,
            'Metadata': metadata,
            'ACL': 'public-read' # Set to public-read for easy sharing
        }

        try:
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                object_name,
                ExtraArgs=extra_args
            )
            
            # Construct the public URL
            url = f"https://{self.bucket_name}.s3.{AWS_REGION_NAME}.amazonaws.com/{object_name}"
            return {'success': True, 'url': url, 'filename': object_name}
        
        except ClientError as e:
            print(f"S3 Upload Error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            print(f"Unexpected Upload Error: {e}")
            return {'success': False, 'error': str(e)}

    def get_history(self, max_keys: int = 10) -> list:
        """
        Retrieves a list of recently uploaded files from the S3 bucket.
        
        :param max_keys: Maximum number of files to retrieve.
        :return: List of dictionaries containing file info.
        """
        if not self.s3_client:
            return []

        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                MaxKeys=max_keys
            )
            
            history = []
            if 'Contents' in response:
                for item in response['Contents']:
                    filename = item['Key']
                    url = f"https://{self.bucket_name}.s3.{AWS_REGION_NAME}.amazonaws.com/{filename}"
                    history.append({
                        'filename': filename,
                        'size': item['Size'],
                        'last_modified': item['LastModified'].isoformat(),
                        'url': url
                    })
            return history
        
        except ClientError as e:
            print(f"S3 History Error: {e}")
            return []
        except Exception as e:
            print(f"Unexpected History Error: {e}")
            return []

# Example Usage (for testing purposes)
if __name__ == '__main__':
    # NOTE: This requires valid credentials in config.py
    aws_service = AWSService()
    
    # Create a dummy file for testing upload
    dummy_file = "test_upload.txt"
    with open(dummy_file, "w") as f:
        f.write("This is a test file for S3 upload.")
        
    print(f"Uploading {dummy_file}...")
    result = aws_service.upload_file(dummy_file, tags="test, dummy", content_type="text/plain")
    print(f"Upload Result: {result}")
    
    if result['success']:
        print("\nRetrieving history...")
        history = aws_service.get_history(max_keys=5)
        for item in history:
            print(f"- {item['filename']} ({item['last_modified']})")
    
    os.remove(dummy_file)
