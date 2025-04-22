from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.clock import Clock

# ตั้งค่าให้เต็มจอ Kiosk Mode
Window.fullscreen = 'auto'

# ฟอนต์ภาษาไทย
FONT_THAI = '/usr/share/fonts/truetype/tlwg/Garuda.ttf'

class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', spacing=20, padding=50)
        
        # เพิ่มรูปภาพใน splash screen
        image = Image(source='screen.jpg', size_hint=(1, 0.6))
        layout.add_widget(image)
        
        # เพิ่มชื่อโปรแกรมและผู้พัฒนา
        title = Label(text='ชื่อโปรแกรม\nผู้พัฒนา: ชื่อคุณ', font_size=32, font_name=FONT_THAI, halign='center')
        layout.add_widget(title)
        
        # ปุ่มเข้าสู่โปรแกรมหลัก
        start_btn = Button(text='เริ่มใช้งาน', size_hint=(None, None), size=(200, 60), font_name=FONT_THAI, background_color=(0, 0.6, 1, 1))
        start_btn.bind(on_release=self.start_program)
        layout.add_widget(start_btn)
        
        self.add_widget(layout)
    
    def start_program(self, instance):
        # เปลี่ยนไปยังหน้าหลัก
        self.manager.current = 'main'

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # ใส่เนื้อหาของโปรแกรมหลักที่ต้องการ
        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        
        title = Label(text='โปรแกรมหลัก', font_size=40, font_name=FONT_THAI, halign='center')
        layout.add_widget(title)
        
        # เพิ่มปุ่มต่างๆ ของโปรแกรมหลักที่นี่
        # ปุ่มตัวอย่าง
        btn = Button(text='กดเพื่อทำอะไรบางอย่าง', font_size=30, size_hint_y=None, height=80, background_color=(0, 0.6, 1, 1), font_name=FONT_THAI)
        layout.add_widget(btn)
        
        self.add_widget(layout)

class KioskApp(App):
    def build(self):
        # สร้าง ScreenManager เพื่อจัดการหลาย ๆ หน้าจอ
        sm = ScreenManager()
        
        # เพิ่ม SplashScreen และ MainScreen
        sm.add_widget(SplashScreen(name='splash'))
        sm.add_widget(MainScreen(name='main'))
        
        # ตั้งเวลาให้โชว์ Splash Screen 3 วินาที
        Clock.schedule_once(self.change_screen, 3)
        
        return sm
    
    def change_screen(self, dt):
        # เปลี่ยนไปยังหน้าหลักหลังจาก 3 วินาที
        self.root.current = 'main'

if __name__ == '__main__':
    KioskApp().run()
