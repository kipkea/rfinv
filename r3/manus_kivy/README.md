# RFID Management System (Kivy + Django API)

โปรเจกต์นี้เป็นแอปพลิเคชัน Kivy ที่เชื่อมต่อกับ Django API ตามโครงสร้าง Swagger

## โครงสร้างโปรเจกต์
- `main.py`: แอปพลิเคชัน Kivy (ปรับปรุงให้รองรับ Django Endpoints และ Bearer Token)
- `api/mock_api.py`: Mock API ที่จำลองโครงสร้างตาม Django Swagger
- `assets/`: โฟลเดอร์สำหรับเก็บทรัพยากร

## การเชื่อมต่อ API (Django)
แอปพลิเคชันจะเชื่อมต่อกับ Endpoints ดังนี้:
- **Login**: `/api/login/` (รับ username/password, คืนค่า token)
- **RFID Tags**: `/api/RFIDTags/` (GET/POST)
- **Inventory**: `/api/inventory/` (POST)
- **Locations**: `/api/Locations/` (POST)
- **Inspections**: `/api/inspections/` (POST)

## วิธีการใช้งาน
1. ติดตั้งไลบรารี: `pip install kivy requests fastapi uvicorn`
2. รัน API (ถ้ายังไม่มี): `python api/mock_api.py`
3. รันแอป: `python main.py`

## หมายเหตุ
- ระบบใช้ **Bearer Token** ในการยืนยันตัวตนหลังจาก Login
- รองรับภาษาไทยในส่วนของ UI
