from kivy.uix.screenmanager import Screen

# Import the tab classes so Kivy can instantiate them when loading the KV file
from screens.tab_import import ImportTagTab
from screens.tab_inventory import InventoryTab
from screens.tab_location import LocationTab
from screens.tab_inspection import InspectionTab
from api_client import api

class MainTabScreen(Screen):
    def initialize_tabs(self):
        # Set current user label
        self.ids.current_user_label.text = f"ผู้ใช้งาน: {api.current_user}"
        
        # Refresh dropdowns and data when logging in
        if 'inventory_tab' in self.ids:
            self.ids.inventory_tab.refresh_rfid_list()
        if 'location_tab' in self.ids:
            self.ids.location_tab.refresh_rfid_list()
        if 'inspection_tab' in self.ids:
            self.ids.inspection_tab.refresh_data()
            
    def do_logout(self):
        # Clear API context
        api.current_user = None
        api.auth_token = None
        api.api_key = None
        if "Authorization" in api.session.headers:
            del api.session.headers["Authorization"]
        if "X-API-KEY" in api.session.headers:
            del api.session.headers["X-API-KEY"]
        
        # Clear login screen fields
        login_screen = self.manager.get_screen('login')
        login_screen.ids.username_input.text = ""
        login_screen.ids.credential_input.text = ""
        login_screen.ids.login_message.text = ""
        
        # Switch to login screen
        self.manager.current = 'login'
