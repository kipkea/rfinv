from kivy.uix.boxlayout import BoxLayout
from api_client import api

class InventoryTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.available_tags = {}  # format: {"rfid_code": id}

    def refresh_rfid_list(self):
        success, data = api.get_rfid_tags()
        if success:
            # Assume data is a list of dicts. We filter for those not used yet.
            # In a real scenario, the backend might filter this. We'll show all that are not locations for now.
            # Or assume we can see them all and select one.
            tags = [tag for tag in data if not tag.get('is_location', False)]
            self.available_tags = {tag['rfid_code']: tag['id'] for tag in tags}
            
            if self.available_tags:
                self.ids.rfid_spinner.values = list(self.available_tags.keys())
                self.ids.rfid_spinner.text = '--- เลือก RFID ---'
            else:
                self.ids.rfid_spinner.values = []
                self.ids.rfid_spinner.text = 'ไม่มี RFID ว่าง'

    def submit_inventory(self):
        selected_code = self.ids.rfid_spinner.text
        name = self.ids.inv_name_input.text
        detail = self.ids.inv_detail_input.text
        
        if selected_code not in self.available_tags or not name:
            return # Should show error
            
        tag_id = self.available_tags[selected_code]
        success, res = api.create_inventory(tag_id, name, detail)
        
        if success:
            self.ids.inv_name_input.text = ""
            self.ids.inv_detail_input.text = ""
            self.refresh_rfid_list()
