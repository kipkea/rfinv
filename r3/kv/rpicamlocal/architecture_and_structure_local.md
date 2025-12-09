# สถาปัตยกรรมโปรแกรมควบคุมกล้อง Raspberry Pi (OpenCV & Local Storage Kivy)

## 1. ภาพรวมสถาปัตยกรรม

โปรแกรมนี้ใช้สถาปัตยกรรมแบบ **Single-Screen Model-View-ViewModel (MVVM)** ที่เรียบง่าย โดยมีจุดประสงค์เพื่อรวมฟังก์ชันทั้งหมดไว้ในหน้าจอเดียว (MainScreen) และเน้นการจัดเก็บไฟล์ในเครื่อง (Local Storage)

| องค์ประกอบ | เทคโนโลยีหลัก | หน้าที่ |
| :--- | :--- | :--- |
| **View (UI)** | Kivy (Python & KV Language) | แสดงผลพรีวิวกล้อง, ปุ่มควบคุมขนาดใหญ่, และใช้ Popups สำหรับการตั้งค่าและข้อมูลเสริม |
| **ViewModel** | Python Classes | จัดการตรรกะของ UI, การสื่อสารระหว่าง View และ Services, การจัดการสถานะของแอปพลิเคชัน |
| **Services (Model)** | OpenCV, Python | โมดูลที่จัดการงานเฉพาะทาง เช่น การควบคุมกล้อง, การจัดเก็บไฟล์ในเครื่อง, การตั้งค่าเครือข่าย |

## 2. โครงสร้างไดเรกทอรี

```
rpi_camera_controller_opencv/
├── main.py                 # Kivy App Entry Point, MainScreen, และ Popups logic
├── config.py               # Configuration settings (Network, File Paths)
├── images/                 # โฟลเดอร์สำหรับเก็บภาพและวิดีโอที่ถ่ายได้
├── services/
│   ├── camera_service.py   # OpenCV frame capture, saving to local storage
│   └── network_service.py  # Network configuration (nmcli/wpa_supplicant logic)
└── kv/
    ├── main_ui.kv          # Single KV file สำหรับ MainScreen (รวมทุกฟีเจอร์)
    ├── settings_popup.kv   # KV สำหรับ Settings Popup (Network)
    └── tagging_popup.kv    # KV สำหรับ Tagging Popup (ชื่อไฟล์, Tags)
```

**การเปลี่ยนแปลงที่สำคัญ:**
*   ลบ `aws_service.py` และ `facebook_service.py`
*   เพิ่มโฟลเดอร์ `images/` สำหรับจัดเก็บไฟล์
*   `camera_service.py` จะถูกปรับปรุงให้บันทึกไฟล์ไปยัง `images/` โดยตรง

## 3. การควบคุมกล้องและ UI

### 3.1. การควบคุมกล้อง (OpenCV)

*   ใช้ `cv2.VideoCapture(0)` ใน `camera_service.py` เพื่อดึงเฟรม
*   แสดงผลพรีวิวโดยการดึงเฟรมจาก `camera_service.py` และแปลงเป็น Kivy `Texture` เพื่ออัปเดต Widget `Image` ใน `main_ui.kv` อย่างต่อเนื่อง

### 3.2. User Interface (Single-Screen & Popups)

*   ใช้ `MainScreen` เพียงหน้าจอเดียว โดยแบ่งพื้นที่เป็น 3 ส่วนหลัก: **Preview Area**, **Control Panel**, และ **Status Bar**
*   ใช้ `Popup` Widget ของ Kivy สำหรับฟังก์ชันที่ต้องการการป้อนข้อมูลชั่วคราว เช่น **Settings** และ **Tagging**
*   ปุ่ม **"ประวัติ"** และ **"แชร์"** จะถูกลบออกจาก UI

## 4. การจัดการไฟล์

*   **Local Storage:** ไฟล์ภาพและวิดีโอจะถูกบันทึกในโฟลเดอร์ `images/`
*   **File Naming:** ใช้ฟังก์ชันใน `camera_service.py` เพื่อสร้างชื่อไฟล์ที่ไม่ซ้ำกันโดยใช้ Timestamp และ UUID
*   **Tagging:** ข้อมูล Tag จะถูกบันทึกไว้ในชื่อไฟล์หรือในไฟล์ Metadata (เช่น ไฟล์ `.txt` คู่กัน) หากต้องการความซับซ้อนน้อยที่สุด จะรวม Tag เข้าไปในชื่อไฟล์ที่ผู้ใช้กำหนด

## 5. การจัดการเครือข่าย

*   **Network Config (`network_service.py`):** โมดูลนี้จะยังคงอยู่เพื่อจัดการการตั้งค่าเครือข่ายผ่าน `SettingsPopup` โดยใช้คำสั่ง Shell (เช่น `nmcli` หรือ `wpa_supplicant`) ซึ่งต้องใช้สิทธิ์ `sudo` บน RPi จริง
