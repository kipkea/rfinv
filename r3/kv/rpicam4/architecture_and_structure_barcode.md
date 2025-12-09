# สถาปัตยกรรมโปรแกรมและโครงสร้างไฟล์: Barcode/QRCode Detection Version

## 1. สถาปัตยกรรม (Architecture)

สถาปัตยกรรมของโปรแกรมจะยังคงเป็นแบบ **Model-View-Controller (MVC)** อย่างหลวมๆ โดยเน้นที่ **Single-Screen UI** และ **Image Processing Pipeline** ที่เพิ่ม **Barcode/QRCode Detection** เข้ามา

1.  **View (Kivy UI):**
    *   `MainScreen` (ใน `main.py` และ `kv/main_ui.kv`) จะเป็นหน้าจอหลัก
    *   เพิ่มปุ่ม **"อ่าน Barcode/QR"**
    *   เพิ่มส่วนแสดงผล **Barcode/QRCode Result** ใน Status Bar หรือ Popup

2.  **Controller (Main App Logic):**
    *   `main.py` จะจัดการการเรียกใช้ `CameraService` และ `BarcodeService`
    *   เพิ่มฟังก์ชัน `toggle_barcode_detection()` เพื่อเปิด/ปิดการตรวจจับ
    *   เพิ่มฟังก์ชัน `display_barcode_result()` เพื่ออัปเดต UI ด้วยผลลัพธ์

3.  **Model/Service Layer:**
    *   `services/camera_service.py`:
        *   เพิ่มเมธอด `get_barcode_data()` เพื่อเรียกใช้ `BarcodeService`
        *   `update_preview` ใน `main.py` จะเรียก `get_processed_frame()` และส่งเฟรมนั้นไปให้ `BarcodeService` เพื่อตรวจจับ
    *   **NEW: `services/barcode_service.py`:**
        *   รับผิดชอบในการใช้ `pyzbar` เพื่อตรวจจับ Barcode/QRCode
        *   เมธอด `detect_and_decode(frame)`: รับเฟรม OpenCV (BGR) และส่งคืนรายการผลลัพธ์ (ข้อมูล, ประเภท, ตำแหน่ง)

## 2. โครงสร้างไฟล์ (File Structure)

```
rpi_camera_controller_opencv/
├── config.py
├── main.py                     # Kivy App, MainScreen, Popups
├── architecture_and_structure_barcode.md # เอกสารนี้
├── installation_guide_barcode.md # คู่มือการติดตั้งใหม่
├── images/                     # โฟลเดอร์สำหรับเก็บภาพ/วิดีโอ
├── kv/
│   └── main_ui.kv              # Kivy Language UI Definition
└── services/
    ├── camera_service.py       # OpenCV Camera Control, Image Processing, Barcode/QR Integration
    ├── network_service.py      # Network Configuration (Simulated)
    └── barcode_service.py      # NEW: pyzbar Barcode/QRCode Detection Logic
```

## 3. การเปลี่ยนแปลงที่สำคัญในโค้ด

### 3.1. `services/barcode_service.py` (ใหม่)

```python
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
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Decode the barcodes
        detections = decode(gray)
        
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
```

### 3.2. `services/camera_service.py` (ปรับปรุง)

*   เพิ่ม `from .barcode_service import BarcodeService`
*   เพิ่ม `self.barcode_service = BarcodeService()` ใน `__init__`
*   เพิ่ม `self.is_barcode_detection_enabled = False` ใน `__init__`
*   เพิ่มเมธอด `toggle_barcode_detection(enable)`
*   ปรับปรุง `get_processed_frame()` เพื่อเรียก `BarcodeService.detect_and_decode()` และวาดกรอบ Barcode/QRCode บนเฟรมหากเปิดใช้งาน

### 3.3. `main.py` (ปรับปรุง)

*   เพิ่ม `self.is_barcode_detection_enabled = BooleanProperty(False)`
*   เพิ่มฟังก์ชัน `toggle_barcode_detection()` เพื่อสลับสถานะและเรียก `camera_service.toggle_barcode_detection()`
*   ปรับปรุง `update_preview` เพื่อรับผลลัพธ์ Barcode/QRCode และอัปเดต Status Bar

### 3.4. `kv/main_ui.kv` (ปรับปรุง)

*   เพิ่มปุ่ม **"อ่าน Barcode/QR"** ที่ผูกกับ `root.toggle_barcode_detection()`
*   ปรับปรุง `status_bar` เพื่อแสดงผลลัพธ์ Barcode/QRCode

## 4. ขั้นตอนการติดตั้งเพิ่มเติม

ผู้ใช้จะต้องติดตั้ง `pyzbar` และ `libzbar0` เพิ่มเติม:

```bash
sudo apt install libzbar0
pip install pyzbar
```
