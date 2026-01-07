from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

class MySimpleApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        label = Label(text='Hello, Kivy!')
        button = Button(text='Click Me')
        button.bind(on_press=self.on_button_press)
        
        layout.add_widget(label)
        layout.add_widget(button)
        
        return layout

    def on_button_press(self, instance):
        print("Button was pressed!")
        print(MySimpleApp.__qualname__)
        
if __name__ == '__main__':
    MySimpleApp().run()
    