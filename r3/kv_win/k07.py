from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scatterlayout import ScatterLayout

from kivy.uix.label import Label

class MySimpleApp(App):
    def build(self):
        #layout = BoxLayout(orientation='vertical')
        #layout = BoxLayout(orientation='horizontal')  
        #layout = GridLayout(rows=2, cols=2)
        #layout = AnchorLayout(anchor_x='center', anchor_y='center')
        #layout = StackLayout(orientation='lr-tb')
        #layout = StackLayout()
        layout = FloatLayout()
        
        
        label = Label(text='Hello, Kivy!',size_hint=(.2,.2),pos=(50,50))
        label2 = Label(text='Apichart',size_hint=(.2,.2),pos=(400,400))
        button = Button(text='Click Me',size_hint=(.2,.2),pos=(150,150))
        button.bind(on_press=self.on_button_press)
        
        
        layout.add_widget(label)
        layout.add_widget(button)
        layout.add_widget(label2)

    def on_button_press(self, instance):
        print("Button was pressed!")
        print(MySimpleApp.__qualname__)
        
if __name__ == '__main__':
    MySimpleApp().run()
    