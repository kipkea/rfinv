from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from api_client import api

class InspectionTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_location_id = None
        self.scanned_inventories = []
        self.location_map = {} # rfid_code -> location_id
        self.inventory_map = {} # rfid_code -> inventory_id

    def refresh_data(self):
        # Fetch locations and inventories to map RFID scans to IDs
        success, loc_data = api.get_locations()
        if success:
            self.location_map = {}
            for loc in loc_data:
                # Based on Django model, rfid_tag is a relation. The API might return nested data or ID.
                # Assuming nested data includes rfid_code, or we need to look it up.
                # If API just returns rfid_tag ID, we might need a separate call.
                # For this example, let's assume Swagger standard serializer: 
                # loc['rfid_tag'] is either an ID or nested object.
                # To be robust, let's assume we map it here or we rely on the backend to accept rfid_code directly.
                pass
                
        # Since scanning returns the RFID string, and our backend expects inventory IDs,
        # we need the API to give us the mapping, OR we change the API to accept RFID codes.
        # The user's swagger /api/inspections/ POST description says: "Logic สำคัญ: รับค่า RFID มาสแกน -> คำนวณของหาย -> ตอบกลับทันที"
        # This implies the backend ALREADY handles receiving RFID strings directly!
        # If the backend handles it, we don't need inventory_ids, just the scanned strings!
        pass

    def on_location_scanned(self, text):
        tag = text.strip()
        if not tag: return
        
        # In a real app, you might verify this tag is a location tag via API.
        # Here we just assume it's correct and enable inventory scanning.
        self.current_location_id = tag # Passing the RFID string, assuming backend handles it
        self.ids.current_location_label.text = f"สถานที่ปัจจุบัน: {tag}"
        
        # Clear inventory list
        self.scanned_inventories = []
        self.ids.inspected_items_list.clear_widgets()
        self.ids.inspection_result_label.text = ""
        
        self.ids.inspect_inv_input.disabled = False
        self.ids.inspect_loc_input.text = ""
        self.ids.inspect_inv_input.focus = True

    def on_inventory_scanned(self, text):
        tag = text.strip()
        if tag and tag not in self.scanned_inventories:
            self.scanned_inventories.append(tag)
            lbl = Label(text=f"{len(self.scanned_inventories)}. {tag}", size_hint_y=None, height=30, halign='left')
            lbl.bind(size=lbl.setter('text_size'))
            self.ids.inspected_items_list.add_widget(lbl)
            
        self.ids.inspect_inv_input.text = ""
        self.ids.inspect_inv_input.focus = True

    def submit_inspection(self):
        if not self.current_location_id:
            self.ids.inspection_result_label.text = "กรุณาสแกน Location ก่อน"
            return
            
        # The Swagger API says it calculates missing items and replies immediately.
        success, res = api.submit_inspection(self.current_location_id, self.scanned_inventories)
        
        if success:
            # Assume backend returns summary like {"total_expected": 10, "total_found": 8, "total_missing": 2}
            # Or similar response based on the Inspection model calculate_results
            total_expected = res.get('total_expected', 0)
            total_found = res.get('total_found', 0)
            total_missing = res.get('total_missing', 0)
            
            msg = f"สำเร็จ! คาดหวัง: {total_expected}, พบ: {total_found}, หาย: {total_missing}"
            self.ids.inspection_result_label.text = msg
            self.ids.inspection_result_label.color = (0, 1, 0, 1)
            
            # Reset
            self.current_location_id = None
            self.ids.current_location_label.text = "สถานที่ปัจจุบัน: ยังไม่ได้เลือก"
            self.ids.inspect_inv_input.disabled = True
            self.scanned_inventories = []
            self.ids.inspected_items_list.clear_widgets()
        else:
            self.ids.inspection_result_label.text = f"เกิดข้อผิดพลาด: {res}"
            self.ids.inspection_result_label.color = (1, 0, 0, 1)
