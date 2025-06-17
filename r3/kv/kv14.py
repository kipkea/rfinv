import threading
import serial
import cv2
import os
import requests
from datetime import datetime
from kivy.uix.button import Button

class RFIDScanner:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.running = False
        self.collected_data = []

    def start(self):
        self.running = True
        threading.Thread(target=self.loop_scan, daemon=True).start()

    def stop(self):
        self.running = False
        self.send_data()

    def loop_scan(self):
        while self.running:
            if self.ser.in_waiting:
                tag = self.ser.readline().decode().strip()
                image_path = self.capture_image(tag)
                self.collected_data.append({'tag': tag, 'image': image_path})
                print(f'เก็บข้อมูล: {tag}, รูปภาพ: {image_path}')

    def capture_image(self, tag):
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        filename = f"rfid_{tag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        path = os.path.join('/home/pi/pictures/', filename)
        if ret:
            cv2.imwrite(path, frame)
        cam.release()
        return path

    def send_data(self):
        for item in self.collected_data:
            try:
                files = {'image': open(item['image'], 'rb')}
                data = {'tag': item['tag']}
                response = requests.post('http://your-api-server/upload', data=data, files=files)
                print(f"ส่ง: {item['tag']} => {response.status_code}")
            except Exception as e:
                print(f"ส่งข้อมูลล้มเหลว: {e}")
        self.collected_data.clear()

# ใน MainScreen เพิ่มปุ่มเรียกใช้

self.rfid_scanner = RFIDScanner()

start_btn = Button(text='เริ่มสแกน RFID', font_size=30, size_hint_y=None, height=80, background_color=(0, 1, 0, 1))
start_btn.bind(on_release=lambda x: self.rfid_scanner.start())
self.add_widget(start_btn)

stop_btn = Button(text='หยุดสแกน RFID และส่งข้อมูล', font_size=30, size_hint_y=None, height=80, background_color=(1, 0, 0, 1))
stop_btn.bind(on_release=lambda x: self.rfid_scanner.stop())
self.add_widget(stop_btn)
