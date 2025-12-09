# สถาปัตยกรรมโปรแกรมควบคุมกล้อง Raspberry Pi (OpenCV & Single-Screen Kivy)

## 1. ภาพรวมสถาปัตยกรรม

โปรแกรมนี้จะใช้สถาปัตยกรรมแบบ **Single-Screen Model-View-ViewModel (MVVM)** ที่เรียบง่าย โดยมีจุดประสงค์เพื่อรวมฟังก์ชันทั้งหมดไว้ในหน้าจอเดียว (MainScreen) เพื่อให้ใช้งานง่ายบนจอสัมผัสของ Raspberry Pi

| องค์ประกอบ | เทคโนโลยีหลัก | หน้าที่ |
| :--- | :--- | :--- |
| **View (UI)** | Kivy (Python & KV Language) | แสดงผลพรีวิวกล้อง, ปุ่มควบคุมขนาดใหญ่, และใช้ Popups สำหรับการตั้งค่าและข้อมูลเสริม |
| **ViewModel** | Python Classes | จัดการตรรกะของ UI, การสื่อสารระหว่าง View และ Services, การจัดการสถานะของแอปพลิเคชัน |
| **Services (Model)** | OpenCV, Boto3, Python | โมดูลที่จัดการงานเฉพาะทาง เช่น การควบคุมกล้อง, การอัปโหลด AWS S3, การตั้งค่าเครือข่าย |

## 2. โครงสร้างไดเรกทอรี

```
rpi_camera_controller_opencv/
├── main.py                 # Kivy App Entry Point, MainScreen, และ Popups logic
├── config.py               # Configuration settings (AWS, Facebook, Network)
├── services/
│   ├── camera_service.py   # OpenCV frame capture, saving, and video recording
│   ├── aws_service.py      # Boto3 S3 upload, history retrieval, and URL generation
│   ├── network_service.py  # Network configuration (nmcli/wpa_supplicant logic)
│   └── facebook_service.py # Facebook sharing logic
└── kv/
    ├── main_ui.kv          # Single KV file สำหรับ MainScreen (รวมทุกฟีเจอร์)
    ├── settings_popup.kv   # KV สำหรับ Settings Popup (AWS, Network)
    ├── tagging_popup.kv    # KV สำหรับ Tagging Popup (ชื่อไฟล์, Tags)
    └── history_popup.kv    # KV สำหรับ History Popup (เรียกดูย้อนหลัง)
```

## 3. การเปลี่ยนแปลงเทคโนโลยีหลัก

### 3.1. การควบคุมกล้อง (OpenCV Integration)

เนื่องจากข้อจำกัดของ Raspberry Pi OS Bookworm ที่ใช้ `libcamera` แทน `V4L2` แบบเดิม ทำให้ `cv2.VideoCapture()` อาจไม่สามารถเข้าถึงกล้อง CSI ได้โดยตรง

| วิธีการเดิม (Picamera2) | วิธีการใหม่ (OpenCV/Hybrid) |
| :--- | :--- |
| ใช้ `Picamera2` โดยตรงในการจับภาพและวิดีโอ | **ใช้ `cv2.VideoCapture(0)` เป็นหลัก** พร้อมคำแนะนำในการติดตั้ง GStreamer หรือใช้ **Hybrid Approach** โดยใช้ `Picamera2` ในการดึงเฟรม และแปลงเป็น `numpy` array เพื่อส่งให้ `cv2` ประมวลผล (เช่น `cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)`) และแสดงผลใน Kivy |
| แสดงผลพรีวิวโดยใช้ `Picamera2.start_preview(Preview.QTGL)` | แสดงผลพรีวิวโดยการดึงเฟรมจาก `camera_service.py` และแปลงเป็น Kivy `Texture` เพื่ออัปเดต Widget `Image` ใน `main_ui.kv` อย่างต่อเนื่อง (Live Feed) |

### 3.2. User Interface (Single-Screen UI)

| วิธีการเดิม (ScreenManager) | วิธีการใหม่ (Single-Screen & Popups) |
| :--- | :--- |
| ใช้ `ScreenManager` เพื่อสลับระหว่าง `MainScreen`, `SettingsScreen`, `HistoryScreen` | ใช้ `MainScreen` เพียงหน้าจอเดียว โดยแบ่งพื้นที่เป็น 3 ส่วนหลัก: **Preview Area**, **Control Panel**, และ **Status Bar** |
| | ใช้ `Popup` Widget ของ Kivy สำหรับฟังก์ชันที่ต้องการการป้อนข้อมูลชั่วคราว เช่น **Settings**, **Tagging**, และ **History View** เพื่อไม่ให้ผู้ใช้หลุดออกจากหน้าจอหลัก |

## 4. โครงสร้าง Single-Screen UI (MainScreen)

`MainScreen` จะใช้ `BoxLayout` หลักในแนวตั้ง (Vertical) และแบ่งพื้นที่ดังนี้:

1.  **Camera Preview Area (70%):** Widget `Image` ขนาดใหญ่สำหรับแสดงผลพรีวิวกล้องแบบสด
2.  **Control Panel (20%):** `GridLayout` ที่มีปุ่มควบคุมขนาดใหญ่ 4-6 ปุ่ม (Capture, Record, Settings, History, Share)
3.  **Status Bar (10%):** `Label` สำหรับแสดงสถานะปัจจุบัน (เช่น "Ready", "Recording...", "Uploading...")

การออกแบบนี้จะเน้นที่ **ปุ่มขนาดใหญ่** และ **พื้นที่พรีวิวที่ชัดเจน** เพื่อให้เหมาะกับการใช้งานบนจอสัมผัสของ Raspberry Pi

## 5. การจัดการไฟล์และการเชื่อมต่อ

*   **AWS S3 (`aws_service.py`):** ใช้ `boto3` ในการอัปโหลดไฟล์ภาพ/วิดีโอไปยัง S3 โดยใช้ `ExtraArgs={'ACL': 'public-read'}` เพื่อให้สามารถแชร์ URL ได้
*   **File Naming:** ใช้ฟังก์ชันใน `camera_service.py` เพื่อสร้างชื่อไฟล์ที่ไม่ซ้ำกันโดยใช้ Timestamp และ UUID
*   **Tagging:** ข้อมูล Tag จะถูกส่งไปพร้อมกับไฟล์เป็น S3 Metadata (`Metadata={'user-tags': tags}`)
*   **Network Config (`network_service.py`):** โมดูลนี้จะจัดการการตั้งค่าเครือข่ายผ่าน `SettingsPopup` โดยใช้คำสั่ง Shell (เช่น `nmcli` หรือ `wpa_supplicant`) ซึ่งต้องใช้สิทธิ์ `sudo` บน RPi จริง
