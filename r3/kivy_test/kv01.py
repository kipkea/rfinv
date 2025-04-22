from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
import os


class MyTabs(TabbedPanel):
    def __init__(self, **kwargs):
        super(MyTabs, self).__init__(**kwargs)
        self.do_default_tab = False  # ไม่ต้องแสดง default tab

        # --- Tab 1 ---
        self.add_widget(self.create_tab("Tab 1", "./assets/p1.jpg"))

        # --- Tab 2 ---
        self.add_widget(self.create_tab("Tab 2", "./assets/p2.jpg"))

        # --- Tab 3: มี ComboBox และ Slider ---
        tab3 = self.create_tab("Settings", "./assets/p3.jpg", include_controls=True)
        self.add_widget(tab3)

        # --- Tab 4: Shutdown ---
        shutdown_tab = self.create_shutdown_tab()
        self.add_widget(shutdown_tab)

    def create_tab(self, title, image_path, include_controls=False):
        tab = TabbedPanelItem(text=title)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        layout.add_widget(Image(source=image_path, size_hint=(1, 0.6)))

        btn = Button(text=f"Click me in {title}", size_hint=(1, 0.2))
        btn.bind(on_press=lambda x: print(f"{title} Button Clicked"))
        layout.add_widget(btn)

        if include_controls:
            spinner = Spinner(
                text='Option 1',
                values=('Option 1', 'Option 2', 'Option 3'),
                size_hint=(1, 0.1)
            )
            layout.add_widget(spinner)

            slider = Slider(min=0, max=100, value=50, size_hint=(1, 0.1))
            layout.add_widget(slider)

        tab.add_widget(layout)
        return tab

    def create_shutdown_tab(self):
        tab = TabbedPanelItem(text="Shutdown")
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        label = Label(text="กดปุ่มด้านล่างเพื่อ Shutdown", font_size=24)
        layout.add_widget(label)

        btn = Button(text="Shutdown", background_color=(1, 0, 0, 1), font_size=20)
        btn.bind(on_press=self.shutdown)
        layout.add_widget(btn)

        tab.add_widget(layout)
        return tab

    def shutdown(self, instance):
        print("Shutting down...")
        os.system("sudo shutdown now")


class MyApp(App):
    def build(self):
        return MyTabs()


if __name__ == '__main__':
    MyApp().run()
