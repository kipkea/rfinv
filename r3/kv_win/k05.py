from kivy.app import App

#App().run() 

class WeatherApp(App):
    for i in range(5):
        print(i)
        
    pass
if __name__ == '__main__':
    WeatherApp().run()


# --- Kivy file: k05,py.kv ---
"""     
BoxLayout:
    orientation: 'vertical'
    Label:
        text: 'Hello, Kivy!'
    Button:
        text: 'Click Me'
"""

# --- End of Kivy file ---



