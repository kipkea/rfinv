import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from smbus2 import SMBus

# --- Hardware Driver Section ---
class INA226_Driver:
    def __init__(self, bus_num=1, address=0x40):
        self.bus = SMBus(bus_num)
        self.address = address
        # Config: Average 16 samples, Conversion time 1.1ms
        # 0x4127 เป็นค่ามาตรฐานที่เสถียรสำหรับงานทั่วไป
        self.write_register(0x00, 0x4527) 

    def write_register(self, reg, value):
        bus_data = [(value >> 8) & 0xFF, value & 0xFF]
        self.bus.write_i2c_block_data(self.address, reg, bus_data)

    def read_register(self, reg):
        data = self.bus.read_i2c_block_data(self.address, reg, 2)
        res = (data[0] << 8) | data[1]
        return res if res <= 32767 else res - 65536

    def get_bus_voltage(self):
        # LSB = 1.25mV
        return self.read_register(0x02) * 0.00125

    def get_current(self, shunt_resistor=0.1):
        # คำนวณจาก Shunt Voltage (LSB = 2.5uV)
        # I = V_shunt / R_shunt
        v_shunt = self.read_register(0x01) * 0.0000025
        return v_shunt / shunt_resistor

# --- UI Section ---
class PowerDashboard(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        self.padding = 50
        self.spacing = 20

        # สร้าง Driver
        try:
            self.sensor = INA226_Driver(address=0x40)
            self.status = "System Ready"
        except Exception as e:
            self.status = f"Error: {e}"

        # ส่วนแสดงผล
        self.val_v = Label(text="0.00 V", font_size='80sp', color=(0, 1, 0.5, 1))
        self.val_i = Label(text="0.000 A", font_size='80sp', color=(0.2, 0.6, 1, 1))
        self.lbl_status = Label(text=self.status, font_size='15sp')

        self.add_widget(Label(text="BUS VOLTAGE", font_size='20sp'))
        self.add_widget(self.val_v)
        self.add_widget(Label(text="CURRENT DRAW", font_size='20sp'))
        self.add_widget(self.val_i)
        self.add_widget(self.lbl_status)

        # สั่งอัปเดตทุก 200ms (5 FPS สำหรับ UI ลื่นๆ)
        Clock.schedule_interval(self.update, 0.2)

    def update(self, dt):
        try:
            v = self.sensor.get_bus_voltage()
            i = self.sensor.get_current(shunt_resistor=0.1) # แก้ค่า R ตามจริง
            
            self.val_v.text = f"{v:.2f} V"
            self.val_i.text = f"{i:.3f} A"
        except:
            self.lbl_status.text = "Sensor Disconnected!"

class INAMonitorApp(App):
    def build(self):
        return PowerDashboard()

if __name__ == '__main__':
    INAMonitorApp().run()