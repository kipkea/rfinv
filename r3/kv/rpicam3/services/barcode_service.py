import cv2
from pyzbar.pyzbar import decode

class BarcodeService:
    def __init__(self):
        pass

    def detect_and_decode(self, frame):
        """
        Detects and decodes Barcodes and QR Codes in a given frame.
        
        :param frame: OpenCV BGR frame (numpy array).
        :return: List of dictionaries with 'data', 'type', and 'rect' (for drawing).
        """
        # Convert to grayscale for better performance and detection
        # Note: pyzbar can handle BGR, but grayscale is often recommended for pre-processing
        # We will use the BGR frame directly as it comes from the camera service
        
        detections = decode(frame)
        
        results = []
        for detection in detections:
            # Extract the data and type
            data = detection.data.decode("utf-8")
            type = detection.type
            
            # Extract bounding box (rect)
            (x, y, w, h) = detection.rect
            
            results.append({
                'data': data,
                'type': type,
                'rect': (x, y, w, h)
            })
            
        return results
