from rest_framework import serializers  
from .models import RFIDTag, Location, Inventory, InventoryImage, Inspection, User


# --- Basic Serializers ---
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        ref_name = 'RvApiUser'

class RFIDTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFIDTag
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    rfid_code = serializers.SlugRelatedField(
        queryset=RFIDTag.objects.all(),
        slug_field='rfid_code',
        source='rfid_tag'
    )
    
    class Meta:
        model = Location
        fields = '__all__'

class InventoryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryImage
        fields = ['id', 'image', 'photographed_at']

class InventorySerializer(serializers.ModelSerializer):
    # เชื่อมโยง rfid_code แทนการใช้ ID เลขลำดับ
    rfid_code = serializers.SlugRelatedField(
        queryset=RFIDTag.objects.filter(is_location=False),
        slug_field='rfid_code',
        source='rfid_tag'
    )

    # แสดงรายละเอียดของ Tag และ Location แทนที่จะโชว์แค่ ID
    #rfid_tag_detail = RFIDTagSerializer(source='rfid_tag', read_only=True)
    current_location_detail = LocationSerializer(source='current_location', read_only=True)
    images = InventoryImageSerializer(many=True, read_only=True) # Nested Images

    class Meta:
        model = Inventory
        fields = '__all__'

# --- Inspection Serializer  ---
class InspectionSerializer(serializers.ModelSerializer):
    """
    ใช้สำหรับแสดงผล (Read)
    """
    # รับรายการ ID ของสินค้าที่สแกนเจอในรูปแบบ List
    found_inventory_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Inventory.objects.all(), 
        source='found_inventories',
        required=False
    )

    location_name = serializers.CharField(source='location.name', read_only=True)
    inspected_by_name = serializers.CharField(source='inspected_by.username', read_only=True)
    
    class Meta:
        model = Inspection
        fields = '__all__'


class InspectionCreateSerializer(serializers.ModelSerializer):
    """
    ใช้สำหรับสร้าง (Write) - รับ List ของ RFID Codes เข้ามา
    """
    # รับค่า array ของ rfid_code เช่น ["E200...", "E201..."]
    scanned_rfid_codes = serializers.ListField(
        child=serializers.CharField(), 
        write_only=True,
        help_text="List of RFID codes scanned by the reader"
    )

    class Meta:
        model = Inspection
        fields = ['location', 'scanned_rfid_codes', 'inspected_by']

    def create(self, validated_data):
        # แยก scanned_rfid_codes ออกมาก่อนส่งให้ create ปกติ
        scanned_codes = validated_data.pop('scanned_rfid_codes', [])
        inspection = super().create(validated_data)
        
        # Logic: แปลง RFID Codes เป็น Inventory Objects
        found_inventories = Inventory.objects.filter(rfid_tag__rfid_code__in=scanned_codes)
        
        # บันทึกลง ManyToMany Field
        inspection.found_inventories.set(found_inventories)
        
        # คำนวณผลลัพธ์ (ตาม Logic ใน Model ที่เราเขียนไว้)
        results = inspection.calculate_results()
        
        # ฝากผลลัพธ์ไว้ที่ instance ชั่วคราวเพื่อส่งกลับไปที่ View
        inspection._temp_results = results 
        return inspection


