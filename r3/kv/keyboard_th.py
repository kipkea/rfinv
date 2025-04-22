from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button

class ThaiKeyboard(GridLayout):
    def __init__(self, target_input, **kwargs):
        super().__init__(**kwargs)
        self.cols = 11
        self.spacing = 5
        self.padding = 10
        self.target = target_input

        font_path = 'THSarabunNew.ttf'
        keys = [
            'ๆ','ไ','ำ','พ','ะ','ั','ี','ร','น','ย','บ',
            'ล','ฃ','ฟ','ห','ก','ด','เ','้','่','า','ส',
            'ว','ง','ฆ','ฐ','ญ','ฐ','ฏ','โ','ฌ','๋','ษ',
            'ณ','ม','ใ','ฝ','Backspace','Space','Enter'
        ]

        for key in keys:
            if key == 'Space':
                btn = Button(text='เว้นวรรค', font_name=font_path, size_hint_x=None, width=300, font_size=30)
                btn.bind(on_release=lambda x: self.insert_text(' '))
            elif key == 'Backspace':
                btn = Button(text='ลบ', font_name=font_path, size_hint_x=None, width=150, font_size=30)
                btn.bind(on_release=lambda x: self.backspace())
            elif key == 'Enter':
                btn = Button(text='ขึ้นบรรทัดใหม่', font_name=font_path, size_hint_x=None, width=200, font_size=30)
                btn.bind(on_release=lambda x: self.insert_text('\n'))
            else:
                btn = Button(text=key, font_size=30)
                btn.bind(on_release=lambda x, font_name=font_path, t=key: self.insert_text(t))
            self.add_widget(btn)

    def insert_text(self, substring):
        self.target.text += substring

    def backspace(self):
        self.target.text = self.target.text[:-1]
