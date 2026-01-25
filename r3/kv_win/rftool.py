import threading
import serial
import time
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.properties import StringProperty

# การตั้งค่า Serial Port (ปรับตามจริง เช่น /dev/ttyUSB0 หรือ /dev/ttyS0)
DEFAULT_PORT = '/dev/ttyAMA0'

class RFIDTester(BoxLayout):
    log_text = StringProperty("Ready...\n")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.ser = None
        self.is_reading = False
        self.read_thread = None
        
        # --- ส่วนที่ 1: การเชื่อมต่อ (Connection) ---
        conn_layout = BoxLayout(size_hint_y=0.1)
        self.port_input = TextInput(text=DEFAULT_PORT, multiline=False)
        self.baud_spinner = Spinner(
            text='38400',
            values=('9600', '19200', '38400', '115200', '230400')
        )
        self.btn_connect = Button(text="Connect")
        self.btn_connect.bind(on_press=self.toggle_connection)
        
        conn_layout.add_widget(Label(text="Port:"))
        conn_layout.add_widget(self.port_input)
        conn_layout.add_widget(Label(text="Baud:"))
        conn_layout.add_widget(self.baud_spinner)
        conn_layout.add_widget(self.btn_connect)
        self.add_widget(conn_layout)

        # --- ส่วนที่ 2: ตั้งค่าเครื่อง (Settings & Info) ---
        setting_layout = GridLayout(cols=4, size_hint_y=0.2)
        
        # ปุ่มอ่าน ID เครื่อง (Command S)
        btn_get_id = Button(text="Get Reader ID")
        btn_get_id.bind(on_press=lambda x: self.send_command("S"))
        
        # ปุ่มอ่านกำลังส่ง (Command N0)
        btn_get_power = Button(text="Get Power")
        btn_get_power.bind(on_press=lambda x: self.send_command("N0,00"))
        
        # ปุ่มตั้งกำลังส่ง (Command N1) - ตัวอย่างตั้งค่า Max (1B = 26.5dBm)
        self.power_spinner = Spinner(text='Max (26dBm)', values=('Min (0dBm)', 'Mid (18dBm)', 'Max (26dBm)'))
        btn_set_power = Button(text="Set Power")
        btn_set_power.bind(on_press=self.set_rf_power)

        # ปุ่มเปลี่ยน Baudrate ถาวร (Command NA)
        btn_set_baud = Button(text="Set Baud to 230400")
        btn_set_baud.bind(on_press=self.set_high_speed)

        setting_layout.add_widget(btn_get_id)
        setting_layout.add_widget(btn_get_power)
        setting_layout.add_widget(self.power_spinner)
        setting_layout.add_widget(btn_set_power)
        setting_layout.add_widget(btn_set_baud)
        self.add_widget(setting_layout)

        # --- ส่วนที่ 3: อ่าน Tag (Operations) ---
        ops_layout = BoxLayout(size_hint_y=0.15)
        
        # อ่าน Tag เดียว (Command Q)
        btn_read_single = Button(text="Read Single (Q)")
        btn_read_single.bind(on_press=lambda x: self.send_command("Q"))
        
        # อ่านหลาย Tag ต่อเนื่อง (Command U Loop)
        self.btn_multi = Button(text="Start Multi-Read (U)")
        self.btn_multi.bind(on_press=self.toggle_multi_read)
        
        ops_layout.add_widget(btn_read_single)
        ops_layout.add_widget(self.btn_multi)
        self.add_widget(ops_layout)

        # --- ส่วนที่ 4: แสดงผล (Log Area) ---
        self.log_display = TextInput(text=self.log_text, readonly=True)
        self.add_widget(self.log_display)
        self.bind(log_text=self._update_log_text)
    '''
    def update_log_display(self, instance, value):
        self.log_display.text = value

    def log(self, msg):
        # เพิ่มข้อความใหม่ไปที่ด้านบนสุด
        Clock.schedule_once(lambda dt: setattr(self, 'log_text', f"{msg}\n" + self.log_text[:5000]))
    '''
    
    # --- แก้ไขส่วน Log ให้ Auto-Scroll ---
    def log(self, msg):
        # ใช้ Clock.schedule_once เพื่อให้แน่ใจว่า UI อัปเดตบน Main Thread
        Clock.schedule_once(lambda dt: self._update_log_text(msg))

    def _update_log_text(self, msg):
        # 1. เพิ่มข้อความใหม่ต่อท้าย (Append)
        # ใช้ \n นำหน้าเพื่อให้ขึ้นบรรทัดใหม่สวยงาม
        new_text = self.log_display.text + f"{msg}\n"
        
        # 2. จำกัดความยาวข้อความ (Buffer limit) 
        # เก็บไว้แค่ 5000 ตัวอักษรล่าสุด เพื่อป้องกันแอปค้างเมื่อรันไปนานๆ
        if len(new_text) > 5000:
            new_text = new_text[-5000:]
            
        self.log_display.text = new_text

        # 3. สั่งให้เลื่อนลงล่างสุด (Auto-Scroll to Bottom)
        # ต้องรอจังหวะเล็กน้อยให้ Text อัปเดตก่อนจึงย้าย Cursor
        Clock.schedule_once(self.scroll_to_bottom, 0.1)

    def scroll_to_bottom(self, dt):
        # ย้าย Cursor ไปที่บรรทัดสุดท้าย คอลัมน์ที่ 0
        # self.log_display._lines คือลิสต์ของบรรทัดทั้งหมด
        self.log_display.cursor = (0, len(self.log_display._lines))
        
    def toggle_connection(self, instance):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None
            self.btn_connect.text = "Connect"
            self.log("Disconnected.")
        else:
            try:
                self.ser = serial.Serial(
                    self.port_input.text, 
                    int(self.baud_spinner.text), 
                    timeout=0.1
                )
                self.btn_connect.text = "Disconnect"
                self.log(f"Connected to {self.port_input.text} at {self.baud_spinner.text}")
                # เริ่ม Thread สำหรับรอรับข้อมูล
                threading.Thread(target=self.serial_listener, daemon=True).start()
            except Exception as e:
                self.log(f"Error: {e}")

    def send_command(self, cmd_str):
        if self.ser and self.ser.is_open:
            # รูปแบบคำสั่ง: <LF>COMMAND<CR> ตามเอกสาร [1]
            full_cmd = b'\x0A' + cmd_str.encode() + b'\x0D'
            self.ser.write(full_cmd)
            self.log(f">> Sent: {cmd_str}")
        else:
            self.log("Error: Serial not connected")

    def serial_listener(self):
        while self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting:
                    # อ่านข้อมูล: Response เริ่มด้วย LF จบด้วย CR LF [1]
                    raw_data = self.ser.read_until(b'\x0D\x0A')
                    decoded = raw_data.decode('ascii', errors='ignore').strip()
                    if decoded:
                        self.log(f"<< Recv: {decoded}")
            except Exception as e:
                self.log(f"Read Error: {e}")
                break
            time.sleep(0.01)

    def set_rf_power(self, instance):
        # คำสั่ง N1,<value> ค่า 00-1B [2], [3]
        val_map = {'Min (0dBm)': '00', 'Mid (18dBm)': '0E', 'Max (26dBm)': '1B'}
        hex_val = val_map.get(self.power_spinner.text, '1B')
        self.send_command(f"N1,{hex_val}")

    def set_high_speed(self, instance):
        # คำสั่ง NA,7 คือตั้งเป็น 230400 bps [4]
        self.send_command("NA,7")
        self.log("Changing baudrate to 230400... Please Re-connect.")
        # หลังจากส่งคำสั่งต้องปิดแล้วเปิดใหม่ด้วย baudrate ใหม่

    def toggle_multi_read(self, instance):
        if not self.is_reading:
            self.is_reading = True
            self.btn_multi.text = "Stop Reading"
            threading.Thread(target=self.multi_read_loop, daemon=True).start()
        else:
            self.is_reading = False
            self.btn_multi.text = "Start Multi-Read (U)"

    def multi_read_loop(self):
        while self.is_reading and self.ser and self.ser.is_open:
            # ส่งคำสั่ง U (Multi-Tag) [5]
            # U อ่านหลาย tag ใน field เดียว หรือจะส่งถี่ๆ ก็ได้
            full_cmd = b'\x0A' + b'U' + b'\x0D'
            self.ser.write(full_cmd)
            time.sleep(0.05) # Delay เล็กน้อยป้องกัน Buffer Overflow

class RFIDApp(App):
    def build(self):
        return RFIDTester()

if __name__ == '__main__':
    RFIDApp().run()