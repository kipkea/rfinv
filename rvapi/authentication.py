# authentication.py (สร้างไฟล์นี้แยกออกมา)
from rest_framework import authentication
from rest_framework import exceptions
from .models import UserAPIKey

class APIKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        # ตรวจสอบ Header ชื่อ X-API-KEY
        api_key = request.META.get('HTTP_X_API_KEY')
        if not api_key:
            return None # ไม่ได้ส่ง Key มา ให้ข้ามไปใช้ระบบ Auth อื่น (เช่น JWT)

        try:
            key_obj = UserAPIKey.objects.get(key=api_key)
        except UserAPIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API Key')

        return (key_obj.user, None) # คืนค่า User กลับไปให้ระบบ
    