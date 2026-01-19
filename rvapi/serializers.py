from rest_framework import serializers  
#from .models import rfinv_loc, rfinv_inv ,rfinv_check  
#from .models import RFIDTag, Location, Inventory, Inspection
from .models import RFIDTag, Location, Inventory, InventoryImage, Inspection, User


# --- Basic Serializers ---

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class RFIDTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFIDTag
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class InventoryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryImage
        fields = ['id', 'image', 'photographed_at']

class InventorySerializer(serializers.ModelSerializer):
    # แสดงรายละเอียดของ Tag และ Location แทนที่จะโชว์แค่ ID
    rfid_tag_detail = RFIDTagSerializer(source='rfid_tag', read_only=True)
    current_location_detail = LocationSerializer(source='current_location', read_only=True)
    images = InventoryImageSerializer(many=True, read_only=True) # Nested Images

    class Meta:
        model = Inventory
        fields = '__all__'

# --- Inspection Serializer (พระเอกของเรา) ---

class InspectionSerializer(serializers.ModelSerializer):
    """
    ใช้สำหรับแสดงผล (Read)
    """
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
    
'''
class StudentSerializer(serializers.ModelSerializer):  
    first_name = serializers.CharField(max_length=200, required=True)  
    last_name = serializers.CharField(max_length=200, required=True)  
    address = serializers.CharField(max_length=200, required=True)  
    roll_number = serializers.IntegerField()  
    mobile = serializers.CharField(max_length=10, required=True)  
  
    class Meta:  
        model = Students  
        fields = ('__all__')  

'''  
'''class rfinv_loc(models.Model):
    Loc_ID = models.CharField(max_length=255,primary_key=True, editable=True, unique=True)
    Loc_Name = models.CharField(max_length=255, blank = True, null = True)
'''

'''
###ก่อนแก้ไข
class RFIDTag_SL(serializers.ModelSerializer):
    RFID = serializers.CharField(max_length=255, required=True)
    is_location = serializers.BooleanField(default=False)

    class Meta:
        model = RFIDTag
        fields = ('__all__')


class Location_SL(serializers.ModelSerializer):
    rfid_tag = RFIDTag_SL()

    class Meta:
        model = Location
        fields = '__all__'

class Inventory_SL(serializers.ModelSerializer):
    rfid_tag = RFIDTag_SL()

    class Meta:
        model = Inventory
        fields = '__all__'


class Inspection_SL(serializers.ModelSerializer):
    rfid_tags = RFIDTag_SL(many=True)

    class Meta:
        model = Inspection
        fields = '__all__'
    
'''      

'''
    def create(self, validated_data):  
        """ 
        Create and return a new `Students` instance, given the validated data. 
        """  
        return rfinv_loc.objects.create(**validated_data)  
  
    def update(self, instance, validated_data):  
        """ 
        Update and return an existing `Students` instance, given the validated data. 
        """  
        instance.Loc_ID = validated_data.get('Loc_ID', instance.Loc_ID)  
        instance.Loc_Name = validated_data.get('Loc_Name', instance.Loc_Name)  
  
        instance.save()  
        return instance  
'''
        
'''    
class rfinv_inv(models.Model):    
    Inv_ID = models.AutoField(primary_key=True, auto_created = True,editable=True, unique=True) 
    Inv_Name = models.CharField(max_length=255, blank = True, null = True)
    Inv_Created = models.DateTimeField(auto_now_add=True)
    Inv_Modified = models.DateTimeField(auto_now=True)
    RFCode = models.CharField(max_length=255, blank = True, null = True)
    
    #เอาไว้เก็บสถานที่เก็บสุดท้าย
    Inv_Last_Check_Time = models.DateTimeField(auto_now_add=True)
    Inv_Last_Loc = models.CharField(max_length=255, blank = True, null = True)
'''        
