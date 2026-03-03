import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Line
from smbus2 import SMBus

# --- Hardware Driver (INA226) ---
class INA226_Driver:
    def __init__(self, bus_num=1, address=0x40):
        try:
            self.bus = SMBus(bus_num)
            self.address = address
            # ปรับ Config: Avg 64 samples เพื่อลด Noise สำหรับ Shunt ค่าต่ำ
            # 0x4727: Avg=64, Vbus/Vsh conv = 1.1ms
            self.write_register(0x00, 0x4727) 
        except Exception as e:
            print(f"Hardware Error: {e}")

    def write_register(self, reg, value):
        bus_data = [(value >> 8) & 0xFF, value & 0xFF]
        self.bus.write_i2c_block_data(self.address, reg, bus_data)

    def read_register(self, reg):
        try:
            data = self.bus.read_i2c_block_data(self.address, reg, 2)
            res = (data[0] << 8) | data[1]
            return res if res <= 32767 else res - 65536
        except: return 0

    def get_data(self, shunt_res=0.01):
        # Bus Voltage (LSB 1.25mV)
        v = self.read_register(0x02) * 0.00125
        # Shunt Voltage (LSB 2.5uV) -> I = V_shunt / R_shunt
        v_shunt = self.read_register(0x01) * 0.0000025
        i = v_shunt / shunt_res
        return v, i

# --- Real-time Graph Widget ---
class RealTimeGraph(BoxLayout):
    def __init__(self, line_color=(0, 1, 0, 1), **kwargs):
        super().__init__(**kwargs)
        self.buffer = [0] * 100
        self.line_color = line_color
        with self.canvas.after:
            Color(*self.line_color)
            self.line = Line(points=[], width=2)

    def update(self, val):
        self.buffer.append(val)
        if len(self.buffer) > 100: self.buffer.pop(0)
        
        # Auto-Scaling Logic
        b_min, b_max = min(self.buffer), max(self.buffer)
        span = b_max - b_min
        if span < 0.001: span = 1.0 # กัน Error กรณีค่านิ่งสนิท
        
        new_points = []
        x_step = self.width / 99
        for i, v in enumerate(self.buffer):
            x = self.x + (i * x_step)
            # ปรับ Y ให้อยู่ในกรอบ 10% - 90% ของความสูง Widget
            y = self.y + ((v - b_min) / span * self.height * 0.8) + (self.height * 0.1)
            new_points.extend([x, y])
        self.line.points = new_points

# --- Main Application UI ---
class PowerMonitorApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)
        self.sensor = INA226_Driver()
        self.r_shunt = 0.01  # <--- แก้ไขตามที่คุณแจ้ง (R010)

        # Voltage Display
        self.lbl_v = Label(text="0.00 V", font_size='50sp', color=(0, 1, 0.6, 1))
        self.graph_v = RealTimeGraph(line_color=(0, 1, 0.6, 1))
        
        # Current Display
        self.lbl_i = Label(text="0.000 A", font_size='50sp', color=(0.1, 0.7, 1, 1))
        self.graph_i = RealTimeGraph(line_color=(0.1, 0.7, 1, 1))

        # Layout Assembly
        self.add_widget(Label(text="VOLTAGE (BUS)", size_hint_y=0.1))
        self.add_widget(self.lbl_v)
        self.add_widget(self.graph_v)
        self.add_widget(Label(text="CURRENT (SHUNT)", size_hint_y=0.1))
        self.add_widget(self.lbl_i)
        self.add_widget(self.graph_i)

        Clock.schedule_interval(self.refresh, 0.1)

    def refresh(self, dt):
        v, i = self.sensor.get_data(shunt_res=self.r_shunt)
        self.lbl_v.text = f"{v:.2f} V"
        self.lbl_i.text = f"{i:.3f} A"
        self.graph_v.update(v)
        self.graph_i.update(i)

class INAMonitor(App):
    def build(self):
        return PowerMonitorApp()

if __name__ == '__main__':
    INAMonitor().run()

    