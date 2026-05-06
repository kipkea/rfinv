from kivy.uix.boxlayout import BoxLayout
from api_client import api

class LocationTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.available_tags = {}

    def refresh_rfid_list(self):
        success, data = api.get_rfid_tags()
        if success:
            # We filter for tags that could be used for locations
            # Depending on backend logic, maybe we just show all unassigned tags.
            tags = [tag for tag in data if not tag.get('is_location', False)] 
            self.available_tags = {tag['rfid_code']: tag['id'] for tag in tags}
            
            if self.available_tags:
                self.ids.loc_rfid_spinner.values = list(self.available_tags.keys())
                self.ids.loc_rfid_spinner.text = '--- เลือก RFID ---'
            else:
                self.ids.loc_rfid_spinner.values = []
                self.ids.loc_rfid_spinner.text = 'ไม่มี RFID ว่าง'

    def submit_location(self):
        selected_code = self.ids.loc_rfid_spinner.text
        name = self.ids.loc_name_input.text
        description = self.ids.loc_detail_input.text
        
        if selected_code not in self.available_tags or not name:
            return
            
        tag_id = self.available_tags[selected_code]
        print(selected_code, tag_id, name, description)
        success, res = api.create_location(tag_id, selected_code, name, description)
        
        if success:
            self.ids.loc_name_input.text = ""
            self.ids.loc_detail_input.text = ""
            self.refresh_rfid_list()
        else:
            print("เกิดข้อผิดพลาดในการสร้างสถานที่:", res)
            # หากมี Label บนหน้าจอ สามารถสั่งให้แสดงข้อผิดพลาดตรงนี้ได้
