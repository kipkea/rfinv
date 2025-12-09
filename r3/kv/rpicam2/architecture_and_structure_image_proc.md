# สถาปัตยกรรมโปรแกรม: RPi Camera Controller (OpenCV & Local Storage with Image Processing)

## 1. ภาพรวมสถาปัตยกรรม

สถาปัตยกรรมนี้ยังคงใช้รูปแบบ **Model-View-Controller (MVC)** อย่างหลวมๆ โดยเน้นที่การเพิ่ม **Image Processing Pipeline** เข้าไปในส่วนของ **Model** (CameraService) และ **View** (MainScreen) เพื่อให้สามารถปรับแต่งภาพแบบ Real-time ได้

## 2. โครงสร้างไฟล์ (File Structure)

```
rpi_camera_controller_opencv/
├── images/                         # โฟลเดอร์สำหรับเก็บภาพและวิดีโอที่บันทึก
├── kv/
│   └── main_ui.kv                  # Kivy Language สำหรับ Single-Screen UI (เพิ่ม UI Controls สำหรับ Image Processing)
├── services/
│   ├── camera_service.py           # Model: ควบคุมกล้อง, Image Processing Pipeline, บันทึกไฟล์
│   └── network_service.py          # Model: จำลองการตั้งค่าเครือข่าย
├── config.py                       # การตั้งค่าตัวแปรคงที่ (เช่น ขนาดภาพเริ่มต้น, โฟลเดอร์)
├── main.py                         # Controller/View: Kivy App หลัก, MainScreen, Popups
└── architecture_and_structure_image_proc.md # เอกสารนี้
```

## 3. Image Processing Pipeline (IPP)

การปรับแต่งภาพแบบ Real-time จะถูกจัดการใน `CameraService.get_processed_frame()` ซึ่งจะถูกเรียกใช้โดย `MainScreen.update_preview()`

### 3.1. Data Flow

1.  **`MainScreen.update_preview()`** เรียก **`CameraService.get_processed_frame()`**
2.  **`CameraService.get_processed_frame()`**
    *   เรียก **`CameraService.get_frame()`** เพื่อดึงเฟรมดิบ (Raw Frame) จาก OpenCV
    *   นำ Raw Frame ไปผ่าน **Image Processing Pipeline** ตามพารามิเตอร์ที่ถูกตั้งค่าไว้ใน `self.processing_params`
    *   ส่ง Processed Frame กลับไป
3.  **`MainScreen.update_preview()`** แปลง Processed Frame เป็น Kivy Texture และแสดงผล

### 3.2. Processing Parameters (ใน `CameraService`)

`CameraService` จะมี Dictionary ชื่อ `self.processing_params` เพื่อเก็บสถานะการปรับแต่งภาพทั้งหมด:

| Parameter | Type | Range/Options | OpenCV Function |
| :--- | :--- | :--- | :--- |
| `brightness` | float | 0.0 to 2.0 (Default 1.0) | `cv2.convertScaleAbs` (alpha) |
| `contrast` | float | 0.0 to 2.0 (Default 1.0) | `cv2.convertScaleAbs` (beta) |
| `sharpness` | int | 0 to 10 (Default 0) | `cv2.filter2D` (Laplacian/Unsharp Mask) |
| `color_mode` | str | 'BGR', 'GRAY', 'HSV' | `cv2.cvtColor` |
| `filter` | str | 'None', 'Sobel', 'Canny' | `cv2.Sobel`, `cv2.Canny` |
| `resize_factor` | float | 0.5 to 2.0 (Default 1.0) | `cv2.resize` |

## 4. การปรับปรุงโมดูลหลัก

### 4.1. `camera_service.py`

*   เพิ่ม `self.processing_params` และเมธอด `set_processing_param(key, value)`
*   เพิ่มเมธอด `get_processed_frame()` ที่ใช้ `cv2.convertScaleAbs`, `cv2.cvtColor`, และฟิลเตอร์ต่างๆ ตามค่าใน `self.processing_params`

### 4.2. `main.py` และ `kv/main_ui.kv`

*   เพิ่ม **Image Processing Popup** (หรือรวมใน SettingsPopup) ที่มี **Kivy Slider** และ **Kivy Dropdown** สำหรับควบคุมพารามิเตอร์ทั้งหมด
*   เพิ่มเมธอด `set_image_param(key, value)` ใน `MainScreen` เพื่อเรียก `CameraService.set_processing_param()`
*   แก้ไข `MainScreen.update_preview()` ให้เรียก `self.camera_service.get_processed_frame()` แทน `self.camera_service.get_frame()`

## 5. การบันทึกไฟล์

เมื่อผู้ใช้กด **ถ่ายภาพ** หรือ **หยุดบันทึก** โปรแกรมจะใช้ **Processed Frame** (ไม่ใช่ Raw Frame) ในการบันทึกไฟล์ เพื่อให้ภาพที่ได้ตรงกับที่ผู้ใช้เห็นบนหน้าจอ
