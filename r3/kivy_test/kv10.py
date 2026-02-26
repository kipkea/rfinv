import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Line
from smbus2 import SMBus

# --- ส่วนของ Hardware Driver (INA226) ---
class INA226_Driver:
    def __init__(self, bus_num=1, address=0x40):
        try:
            self.bus = SMBus(bus_num)
            self.address = address
            # Configuration: 0x4527 (Avg 16 samples, 1.1ms conversion)
            self.write_register(0x00, 0x4527)
        except Exception as e:
            print(f"Hardware Init Error: {e}")

    def write_register(self, reg, value):
        bus_data = [(value >> 8) & 0xFF, value & 0xFF]
        self.bus.write_i2c_block_data(self.address, reg, bus_data)

    def read_register(self, reg):
        try:
            data = self.bus.read_i2c_block_data(self.address, reg, 2)
            res = (data[0] << 8) | data[1]
            return res if res <= 32767 else res - 65536
        except:
            return 0

    def get_data(self, shunt_res=0.1):
        # อ่าน Voltage (LSB = 1.25mV)
        v = self.read_register(0x02) * 0.00125
        # อ่าน Current ผ่าน Shunt Voltage (LSB = 2.5uV)
        v_shunt = self.read_register(0x01) * 0.0000025
        i = v_shunt / shunt_res
        return v, i

# --- ส่วนของ Widget กราฟ (Custom Graph) ---
class MiniGraph(BoxLayout):
    def __init__(self, line_color=(0, 1, 0, 1), **kwargs):
        super().__init__(**kwargs)
        self.points = []
        self.max_points = 100
        self.line_color = line_color
        with self.canvas.after:
            Color(*self.line_color)
            self.line = Line(points=[], width=1.5)

    def update_value(self, value):
        self.points.append(value)
        if len(self.points) > self.max_points:
            self.points.pop(0)

        if not self.points: return

        # Auto-Scale: หาค่า Min/Max ในบัฟเฟอร์เพื่อปรับกราฟให้เห็นการขยับ
        v_min, v_max = min(self.points), max(self.points)
        diff = v_max - v_min
        if diff == 0: diff = 0.01 # ป้องกันหารศูนย์

        final_points = []
        x_step = self.width / (self.max_points - 1)
        
        for idx, val in enumerate(self.points):
            x = self.x + (idx * x_step)
            # Normalize y ให้อยู่ในกรอบของ Widget (0.1 - 0.9 ของความสูง)
            norm_y = (val - v_min) / diff
            y = self.y + (norm_y * self.height * 0.8) + (self.height * 0.1)
            final_points.extend([x, y])
            
        self.line.points = final_points

# --- ส่วนของหน้าจอหลัก (Main UI) ---
class PowerMonitorUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=20, spacing=15, **kwargs)
        
        # Setup Hardware
        self.sensor = INA226_Driver(address=0x40)
        self.shunt_value = 0.1 # แก้เป็นค่า R ที่คุณใช้ (R100 = 0.1)

        # UI: Voltage Section
        self.add_widget(Label(text="[b]VOLTAGE (V)[/b]", markup=True, size_hint_y=0.1))
        self.lbl_v = Label(text="0.00 V", font_size='60sp', color=(0, 1, 0.5, 1), size_hint_y=0.2)
        self.add_widget(self.lbl_v)
        self.graph_v = MiniGraph(line_color=(0, 1, 0.5, 1), size_hint_y=0.25)
        self.add_widget(self.graph_v)

        # UI: Current Section
        self.add_widget(Label(text="[b]CURRENT (A)[/b]", markup=True, size_hint_y=0.1))
        self.lbl_i = Label(text="0.000 A", font_size='60sp', color=(0.2, 0.7, 1, 1), size_hint_y=0.2)
        self.add_widget(self.lbl_i)
        self.graph_i = MiniGraph(line_color=(0.2, 0.7, 1, 1), size_hint_y=0.25)
        self.add_widget(self.graph_i)

        # Loop Update ทุกๆ 100ms
        Clock.schedule_interval(self.update_screen, 0.1)

    def update_screen(self, dt):
        v, i = self.sensor.get_data(shunt_res=self.shunt_value)
        
        # อัปเดตตัวเลข
        self.lbl_v.text = f"{v:.2f} V"
        self.lbl_i.text = f"{i:.3f} A"
        
        # อัปเดตกราฟ
        self.graph_v.update_value(v)
        self.graph_i.update_value(i)

class INA_SmartMonitor(App):
    def build(self):
        return PowerMonitorUI()

if __name__ == '__main__':
    INA_SmartMonitor().run()