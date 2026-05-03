from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.text import LabelBase
from kivy.core.window import Window
import os

# Register Thai font
font_path = os.path.join('fonts', 'Kanit-Regular.ttf')
if os.path.exists(font_path):
    LabelBase.register(name='Kanit', fn_regular=font_path)

# Set window size for desktop-like feel
Window.size = (1024, 768)

# Import screens
from screens.login import LoginScreen
from screens.main_tabs import MainTabScreen

class RFIDApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screens = {}

    def build(self):
        # Load the KV file
        Builder.load_file('kv/app_layout.kv')
        
        # Create ScreenManager
        sm = ScreenManager()
        
        # Initialize screens
        self.screens['login'] = LoginScreen()
        self.screens['main_tabs'] = MainTabScreen()
        
        # Add screens to manager
        sm.add_widget(self.screens['login'])
        sm.add_widget(self.screens['main_tabs'])
        
        return sm

if __name__ == '__main__':
    RFIDApp().run()
