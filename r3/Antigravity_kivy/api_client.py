import requests
import json
import os

class APIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self.auth_token = "94QH9mzL.QfDe1xGDKMwIYzjmdzRVUdCU6RCv78wv"
        self.api_key = "V7bp82r4-aHWBrTCALKfOAcDTgeIPeZVXaRk6BsZi6g"
        self.current_user = None
        self.current_user_id = None
        
    def _fetch_user_id(self):
        url = f"{self.base_url}/users/"
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    if user.get("username") == self.current_user:
                        self.current_user_id = user.get("id")
                        break
        except Exception:
            pass
        
    def login(self, username, password):
        url = f"{self.base_url}/api/login/"
        payload = {"username": username, "password": password}
        try:
            # We assume the login endpoint returns a token or sets a session cookie
            response = self.session.post(url, json=payload, timeout=5)
            if response.status_code in [200, 201]:
                data = response.json()
                self.current_user = username
                # Check for token or API Key
                if "token" in data:
                    self.auth_token = data["token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    print(f"Token: {self.auth_token}")  
                elif "key" in data:
                    self.api_key = data["key"]
                    self.session.headers.update({"X-API-KEY": self.api_key})
                    print(f"API Key: {self.api_key}")
                self._fetch_user_id()
                return True, "Login successful"
            else:
                return False, f"Login failed: {response.status_code} - {response.text}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
            
    def login_api_key(self, api_key):
        self.api_key = api_key
        self.current_user = None
        self.current_user_id = None
        
        # กำหนด Header สำหรับ API Key ตาม Swagger (X-API-KEY)
        self.session.headers.update({"X-API-KEY": self.api_key})
        
        # บางระบบที่ใช้ Django Rest Framework API Key อาจคาดหวัง Authorization Header ด้วย
        self.session.headers.update({"Authorization": f"Api-Key {self.api_key}"})
        
        # ทดสอบการใช้งาน API Key โดยเรียกดู /api/RFIDTags/ แทน /users/ เพราะ /users/ อาจจะติดสิทธิ์ Admin
        url = f"{self.base_url}/api/RFIDTags/"
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code != 200:
                return False, f"Invalid API Key ({response.status_code}): {response.text}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
            
        # พยายามดึง user จาก API
        me_url = f"{self.base_url}/users/me/"
        try:
            r = self.session.get(me_url, timeout=5)
            if r.status_code == 200:
                user_data = r.json()
                self.current_user = user_data.get("username")
                self.current_user_id = user_data.get("id")
                
                if not self.current_user or not self.current_user_id:
                    return False, "API /users/me/ ส่งข้อมูลกลับมาไม่ครบ (ขาด username หรือ id)"
                    
                return True, "Login successful"
            else:
                # ถ้าไม่ได้ 200 แสดงว่า API ยังมีปัญหา หรือสิทธิ์ยังไม่ถูกต้อง
                return False, f"ไม่สามารถดึงข้อมูล User ได้ ({r.status_code}): {r.text}"
        except Exception as e:
            return False, f"ไม่สามารถเชื่อมต่อกับ /users/me/ ได้: {str(e)}"
            
    def get_rfid_tags(self):
        url = f"{self.base_url}/api/RFIDTags/"
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                return True, response.json()
            return False, f"Failed to get tags: {response.status_code}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def create_rfid_tag(self, rfid_code, is_location=False):
        url = f"{self.base_url}/api/RFIDTags/"
        payload = {"rfid_code": rfid_code, "is_location": is_location}
        if self.current_user_id:
            payload["registered_by"] = self.current_user_id
            
        try:
            response = self.session.post(url, json=payload, timeout=5)
            if response.status_code in [200, 201]:
                return True, response.json()
            return False, f"Failed to create tag: {response.text}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def create_location(self, rfid_tag_id, name, description=""):
        url = f"{self.base_url}/api/Locations/"
        payload = {
            "rfid_tag": rfid_tag_id,
            "name": name,
            "description": description
        }
        if self.current_user_id:
            payload["created_by"] = self.current_user_id
            
        try:
            response = self.session.post(url, json=payload, timeout=5)
            if response.status_code in [200, 201]:
                return True, response.json()
            return False, f"Failed to create location: {response.text}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def create_inventory(self, rfid_tag_id, name, detail="", image_path=None):
        url = f"{self.base_url}/api/inventory/"
        data = {
            "rfid_tag": rfid_tag_id,
            "name": name,
            "detail": detail
        }
        if self.current_user_id:
            data["registered_by"] = self.current_user_id
            
        try:
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    files = {'image': f}
                    response = self.session.post(url, data=data, files=files, timeout=10)
            else:
                response = self.session.post(url, json=data, timeout=5)
                
            if response.status_code in [200, 201]:
                return True, response.json()
            return False, f"Failed to create inventory: {response.text}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def submit_inspection(self, location_id, found_inventory_ids):
        """
        Submits an inspection to /api/inspections/
        """
        url = f"{self.base_url}/api/inspections/"
        payload = {
            "location": location_id,
            "found_inventories": found_inventory_ids
        }
        if self.current_user_id:
            payload["inspected_by"] = self.current_user_id
            
        try:
            response = self.session.post(url, json=payload, timeout=10)
            if response.status_code in [200, 201]:
                return True, response.json()
            return False, f"Failed to submit inspection: {response.text}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def get_locations(self):
        url = f"{self.base_url}/api/Locations/"
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                return True, response.json()
            return False, f"Failed to get locations: {response.status_code}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def get_inventories(self):
        url = f"{self.base_url}/api/inventory/"
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                return True, response.json()
            return False, f"Failed to get inventory list: {response.status_code}"
        except Exception as e:
            return False, f"Error: {str(e)}"

# A global instance to be used across the app
api = APIClient()
