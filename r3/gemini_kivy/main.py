import os
import requests
from kivy.app import App
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty, StringProperty
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

API_BASE_URL = "http://localhost:8000"

KV_PATH = os.path.join(os.path.dirname(__file__), "app.kv")

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arialuni.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
    r"C:\Windows\Fonts\Arial.ttf",
    r"C:\Windows\Fonts\Tahoma.ttf",
]

for font_path in FONT_CANDIDATES:
    if os.path.isfile(font_path):
        LabelBase.register(name="Roboto", fn_regular=font_path)
        break

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.token = None
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _url(self, path):
        if path.startswith("http"):
            return path
        return f"{self.base_url}{path}"

    def login(self, username, password):
        candidate_paths = [
            "/api/token/",
            "/api/login/",
            "/auth/login/",
            "/api/auth/login/",
        ]
        data = {"username": username, "password": password}
        for path in candidate_paths:
            try:
                response = self.session.post(self._url(path), json=data, timeout=10)
            except requests.RequestException:
                continue
            if response.status_code not in (200, 201):
                continue
            payload = response.json()
            if isinstance(payload, dict):
                if "access" in payload:
                    self.token = payload["access"]
                    self.headers["Authorization"] = f"Bearer {self.token}"
                    return True, "Authenticated with JWT token."
                if "token" in payload:
                    self.token = payload["token"]
                    self.headers["Authorization"] = f"Token {self.token}"
                    return True, "Authenticated with Token."
                if payload.get("success") or payload.get("authenticated"):
                    return True, "Authenticated successfully."
        return False, "Login failed. Please verify your username/password and API login path."

    def _request(self, method, path, **kwargs):
        url = self._url(path)
        headers = kwargs.pop("headers", {})
        merged = {**self.headers, **headers}
        try:
            response = self.session.request(method, url, headers=merged, timeout=15, **kwargs)
            response.raise_for_status()
            if response.status_code == 204:
                return None
            return response.json()
        except requests.HTTPError as exc:
            raise RuntimeError(f"API request failed: {exc} - {getattr(exc.response, 'text', '')}")
        except requests.RequestException as exc:
            raise RuntimeError(f"API request failed: {exc}")

    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def post(self, path, json=None, files=None):
        if files:
            headers = {"Accept": "application/json"}
            return self._request("POST", path, headers=headers, data=json, files=files)
        return self._request("POST", path, json=json)

    def patch(self, path, json=None):
        return self._request("PATCH", path, json=json)

    def get_tags(self, params=None):
        return self.get("/api/RFIDTags/", params=params)

    def get_locations(self):
        return self.get("/api/Locations/")

    def get_inventories(self):
        return self.get("/api/inventory/")

    def find_tag(self, code):
        items = self.get_tags(params={"rfid_code": code})
        if isinstance(items, list) and items:
            return items[0]
        if isinstance(items, dict) and items.get("results"):
            return items["results"][0]
        return None

    def create_tag(self, code, is_location=False):
        payload = {"rfid_code": code, "is_location": is_location}
        return self.post("/api/rfid-tags/", json=payload)

    def create_inventory(self, tag_id, name, detail, image_path=None):
        json_payload = {"rfid_tag": tag_id, "name": name, "detail": detail}
        if image_path and os.path.isfile(image_path):
            with open(image_path, "rb") as stream:
                files = {"image": stream}
                return self.post("/api/inventory/", json=json_payload, files=files)
        return self.post("/api/inventory/", json=json_payload)

    def create_location(self, tag_id, name, description):
        payload = {"rfid_tag": tag_id, "name": name, "description": description}
        return self.post("/api/locations/", json=payload)

    def create_inspection(self, location_id, inventory_ids, inspected_at=None):
        payload = {
            "location": location_id,
            "found_inventories": inventory_ids,
        }
        if inspected_at:
            payload["inspected_at"] = inspected_at
        return self.post("/api/inspections/", json=payload)

class FileChooserPopup(Popup):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

class MissingItemsPopup(Popup):
    def __init__(self, missing_items, api_client, **kwargs):
        super().__init__(**kwargs)
        self.title = "Missing Items (รายการสินค้าที่ไม่พบ)"
        self.size_hint = (0.9, 0.9)
        self.api_client = api_client
        self.missing_items = missing_items

        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        for item in missing_items:
            item_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
            lbl = Label(text=f"{item.get('name', 'Unknown')} (ID: {item.get('id')})")
            btn = Button(text="Remove (จำหน่าย)", size_hint_x=None, width=150)
            btn.bind(on_release=lambda b, inv_id=item['id'], box=item_box: self.remove_item(inv_id, box))

            item_box.add_widget(lbl)
            item_box.add_widget(btn)
            grid.add_widget(item_box)

        scroll.add_widget(grid)
        layout.add_widget(scroll)

        close_btn = Button(text="Close", size_hint_y=None, height=50)
        close_btn.bind(on_release=self.dismiss)
        layout.add_widget(close_btn)

        self.content = layout

    def remove_item(self, inv_id, box):
        try:
            self.api_client.patch(f"/api/inventory/{inv_id}/", json={"current_location": None})
            if box.parent:
                box.parent.remove_widget(box)
        except Exception as e:
            print(f"Failed to remove location for inventory {inv_id}: {e}")

class MainScreen(Screen):
    import_status = StringProperty("")
    inventory_status = StringProperty("")
    location_status = StringProperty("")
    inspection_status = StringProperty("")
    inventory_codes = ListProperty([])
    location_codes = ListProperty([])
    location_options = ListProperty([])

    def load_all_options(self):
        self.refresh_tag_lists()
        self.refresh_locations()

    def refresh_tag_lists(self):
        try:
            client = App.get_running_app().client
            
            # 1. โหลด Tag สำหรับนำไปใช้ลงทะเบียน Inventory (ต้องไม่ใช่ Location และต้องยังไม่ถูกใช้)
            inv_tags = client.get_tags(params={"is_location": "false", "is_used": "false"})
            if isinstance(inv_tags, dict) and "results" in inv_tags:
                inv_tags = inv_tags["results"]
            self.inventory_codes = [tag["rfid_code"] for tag in inv_tags]

            # 2. โหลด Tag สำหรับระบุ Location (ต้องเป็น Location)
            loc_tags = client.get_tags(params={"is_location": "true"})
            if isinstance(loc_tags, dict) and "results" in loc_tags:
                loc_tags = loc_tags["results"]
            self.location_codes = [tag["rfid_code"] for tag in loc_tags]
        except Exception as exc:
            self.inventory_status = f"Cannot load tags: {exc}"

    def refresh_locations(self):
        try:
            locations = App.get_running_app().client.get_locations()
            if isinstance(locations, dict) and "results" in locations:
                locations = locations["results"]
            self.location_options = [loc["name"] for loc in locations]
        except Exception as exc:
            self.location_status = f"Cannot load locations: {exc}"

    def import_rfid_tags(self):
        raw = self.ids.import_input.text.strip()
        if not raw:
            self.import_status = "Enter scanned RFID codes."
            return
        codes = [code.strip() for code in raw.replace(",", "\n").splitlines() if code.strip()]
        if not codes:
            self.import_status = "No valid RFID codes found."
            return
        created = 0
        skipped = 0
        errors = []
        client = App.get_running_app().client
        for code in codes:
            try:
                existing = client.find_tag(code)
                if existing:
                    skipped += 1
                    continue
                client.create_tag(code)
                created += 1
            except Exception as exc:
                errors.append(f"{code}: {exc}")
        self.import_status = f"Imported {created} new tags, skipped {skipped}."
        if errors:
            self.import_status += " Errors: " + "; ".join(errors[:3])
        self.ids.import_input.text = ""
        self.refresh_tag_lists()

    def choose_image(self):
        content = FileChooserPopup(load=self.load_image, cancel=self.dismiss_popup)
        content.open()
        self._popup = content

    def load_image(self, path, filename):
        if not filename:
            return
        self.ids.inventory_image_path.text = os.path.join(path, filename[0])
        self.dismiss_popup()

    def dismiss_popup(self):
        if hasattr(self, "_popup"):
            self._popup.dismiss()

    def register_inventory(self):
        tag_code = self.ids.inventory_tag_spinner.text
        name = self.ids.inventory_name.text.strip()
        detail = self.ids.inventory_detail.text.strip()
        image_path = self.ids.inventory_image_path.text.strip()
        if not tag_code or tag_code == "Select RFID tag":
            self.inventory_status = "Choose an RFID code for the inventory."
            return
        if not name:
            self.inventory_status = "Enter a product name."
            return
        try:
            tag = App.get_running_app().client.find_tag(tag_code)
            if not tag:
                self.inventory_status = "RFID tag not found."
                return
            response = App.get_running_app().client.create_inventory(tag["id"], name, detail, image_path)
            self.inventory_status = f"Inventory '{response.get('name', name)}' registered successfully."
            self.ids.inventory_name.text = ""
            self.ids.inventory_detail.text = ""
            self.ids.inventory_image_path.text = ""
        except Exception as exc:
            self.inventory_status = f"Failed to register inventory: {exc}"

    def register_location(self):
        tag_code = self.ids.location_tag_spinner.text
        name = self.ids.location_name.text.strip()
        description = self.ids.location_description.text.strip()
        if not tag_code or tag_code == "Select RFID tag":
            self.location_status = "Choose an RFID code for the location."
            return
        if not name:
            self.location_status = "Enter a location name."
            return
        try:
            tag = App.get_running_app().client.find_tag(tag_code)
            if not tag:
                self.location_status = "RFID tag not found."
                return
            response = App.get_running_app().client.create_location(tag["id"], name, description)
            self.location_status = f"Location '{response.get('name', name)}' created."
            self.ids.location_name.text = ""
            self.ids.location_description.text = ""
            self.refresh_locations()
        except Exception as exc:
            self.location_status = f"Failed to create location: {exc}"

    def inspect_location(self):
        location_name = self.ids.inspection_location_spinner.text
        raw = self.ids.inspection_input.text.strip()
        if not location_name or location_name == "Select location":
            self.inspection_status = "Choose a location."
            return
        if not raw:
            self.inspection_status = "Enter scanned inventory RFID codes."
            return
        codes = [code.strip() for code in raw.replace(",", "\n").splitlines() if code.strip()]
        if not codes:
            self.inspection_status = "No valid RFID codes found."
            return
        client = App.get_running_app().client
        try:
            locations = client.get_locations()
            if isinstance(locations, dict) and "results" in locations:
                locations = locations["results"]
            chosen = next((loc for loc in locations if loc.get("name") == location_name), None)
            if not chosen:
                self.inspection_status = "Selected location is not available."
                return

            all_inventories = client.get_inventories()
            if isinstance(all_inventories, dict) and "results" in all_inventories:
                all_inventories = all_inventories["results"]
                
            def get_loc_id(inv):
                loc = inv.get("current_location")
                return loc.get("id") if isinstance(loc, dict) else loc
                
            expected_items = [inv for inv in all_inventories if get_loc_id(inv) == chosen["id"]]

            inventory_ids = []
            missing = []
            for code in codes:
                tag = client.find_tag(code)
                if not tag:
                    missing.append(code)
                    continue
                if tag.get("is_location"):
                    continue
                inventory = client.get("/api/inventory/", params={"rfid_tag": tag["id"]})
                if isinstance(inventory, dict) and "results" in inventory:
                    inventory = inventory["results"]
                if isinstance(inventory, list) and inventory:
                    inventory_ids.append(inventory[0]["id"])
                else:
                    missing.append(code)
            response = client.create_inspection(chosen["id"], inventory_ids)
            found = len(inventory_ids)
            self.inspection_status = f"Inspection logged. Found {found} inventories. Missing or invalid codes: {', '.join(missing[:5])}."
            self.ids.inspection_input.text = ""

            found_set = set(inventory_ids)
            actual_missing_items = [item for item in expected_items if item["id"] not in found_set]
            if actual_missing_items:
                popup = MissingItemsPopup(actual_missing_items, client)
                popup.open()

        except Exception as exc:
            self.inspection_status = f"Inspection failed: {exc}"

class RootWidget(ScreenManager):
    pass

class RFinvApp(App):
    def build(self):
        self.client = APIClient(API_BASE_URL)
        if os.path.exists(KV_PATH):
            return Builder.load_file(KV_PATH)
        return RootWidget()

    def on_start(self):
        if self.root:
            main_screen = self.root.get_screen("main")
            if main_screen:
                main_screen.load_all_options()

if __name__ == "__main__":
    RFinvApp().run()
