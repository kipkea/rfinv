from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth import get_user_model

# ใช้ get_user_model() เพื่ออ้างถึง User Model ของ Django
User = get_user_model()

# Create your models here.
    
class RFIDTag(models.Model):
    #RFID = models.CharField(max_length=100, unique=True)
    rfid_code = models.CharField(max_length=100, unique=True, db_index=True)
    is_location = models.BooleanField(default=False)

    # เก็บข้อมูลการลงทะเบียน Tag
    #recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    #recorded_at = models.DateTimeField(auto_now_add=True)
    registered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='registered_tags')
    registered_at = models.DateTimeField(auto_now_add=True)    

    class Meta:
        #db_table = "RFIDTag"
        #ordering = ('RFID',)     
        db_table = "rfid_tag"
        verbose_name = "RFID Tag"
        ordering = ('rfid_code',)  
        
    def __str__(self):
        #return self.RFID
        return f"{self.rfid_code} ({'Location' if self.is_location else 'Item'})"

    
class Location(models.Model):    
    #rfid_tag = models.OneToOneField(RFIDTag, on_delete=models.CASCADE)
    #name = models.CharField(max_length=255, blank = True, null = True)
    
    rfid_tag = models.OneToOneField(RFIDTag, on_delete=models.CASCADE, related_name='location_profile')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
   
       
    #recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    #recorded_at = models.DateTimeField(auto_now_add=True)
    # ใครเป็นคนสร้าง Location นี้ในระบบ
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        #db_table = "Location"
        db_table = "location"
        #ordering = ('rfid_tag',)        

    def __str__(self):
        return self.name
    
class Inventory(models.Model): #res
    #rfid_tag = models.OneToOneField(RFIDTag, on_delete=models.CASCADE)
    #name = models.CharField(max_length=255)
    rfid_tag = models.OneToOneField(RFIDTag, on_delete=models.CASCADE, related_name='inventory_profile')
    name = models.CharField(max_length=255)
    detail = models.TextField(blank=True, null=True)    
    
    # รูปภาพหลักของสินค้า (Profile Image) ตามที่โจทย์ระบุว่าตอนลงทะเบียนมีรูปด้วย
    image = models.ImageField(upload_to='inventory_profiles/', blank=True, null=True)
       
    #recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    #recorded_at = models.DateTimeField(auto_now_add=True)
    # ใครเป็นคนลงทะเบียนสินค้านี้
    registered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    
    #เอาไว้เก็บสถานที่เก็บสุดท้าย
    #Inv_Last_Check_Time = models.DateTimeField(auto_now_add=True, blank = True, null = True)
    #Inv_Last_Loc = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank = True,)
    last_seen_at = models.DateTimeField(auto_now=True, help_text="เวลาล่าสุดที่ระบบพบสินค้านี้")
    current_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_items')


    class Meta:
        #db_table = ('Inventory',)
        #ordering = ('rfid_tag',)    
        db_table = 'inventory'
        ordering = ('name',)            

    def __str__(self):
        return self.name
 
class InventoryImage(models.Model):
    """
    เก็บรูปภาพเพิ่มเติม หรือรูปหลักฐานตอนตรวจสอบ (Inspection Evidence)
    """    
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='evidence_images')
    image = models.ImageField(upload_to='inventory_evidence/%Y/%m/%d/')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    photographed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    photographed_at = models.DateTimeField(default=timezone.now)
    
    # GPS (Optional)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    
    #inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='images')
    #image = models.ImageField(upload_to='inventory_images/%Y/%m/%d/')
    #location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    #photographed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    #photographed_at = models.DateTimeField(default=timezone.now)
    #latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="GPS Latitude")
    #longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, help_text="GPS Longitude")

    class Meta:
        ordering = ['-photographed_at']

    def __str__(self):
        return f"Image for {self.inventory.name} taken at {self.photographed_at.strftime('%Y-%m-%d')}"

class Inspection(models.Model):
    """
    บันทึกการตรวจสอบสินทรัพย์ ณ สถานที่และเวลาที่กำหนด
    """
    # ระบุสถานที่ที่ทำการตรวจสอบอย่างชัดเจน ป้องกันการลบสถานที่หากมีการอ้างอิงถึง
    #location = models.ForeignKey(Location, on_delete=models.PROTECT, help_text="สถานที่ที่ทำการตรวจสอบ")
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='inspections')
    
    
    

    # รายการสินทรัพย์ทั้งหมดที่พบในการตรวจสอบครั้งนี้
    #inspected_inventories = models.ManyToManyField(Inventory, related_name='inspections', blank=True)
    inspected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # ผู้ที่ทำการตรวจสอบ
    #inspected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # วันที่และเวลาที่ตรวจสอบ (ใช้ default=timezone.now เพื่อให้สามารถแก้ไขย้อนหลังได้)
    inspected_at = models.DateTimeField(default=timezone.now)
    
    # เก็บสรุปผล (Optional แต่แนะนำให้มีเพื่อความเร็วในการดู Report ย้อนหลัง)
    total_expected = models.IntegerField(default=0, help_text="จำนวนที่ควรจะมี")
    total_found = models.IntegerField(default=0, help_text="จำนวนที่เจอจริง")
    total_missing = models.IntegerField(default=0, help_text="จำนวนที่หาย")
    

    class Meta:
        # เรียงลำดับจากรายการล่าสุดไปเก่าสุด
        ordering = ('-inspected_at',)

    def __str__(self):
        #location_name = self.location.name if self.location else "N/A"
        #return f"Inspection at {location_name} on {self.inspected_at.strftime('%Y-%m-%d')}"
        return f"Check {self.location.name} at {self.inspected_at.strftime('%Y-%m-%d %H:%M')}"
    
    def calculate_results(self):
        """
        ฟังก์ชันสำหรับคำนวณยอด ของหาย (Missing) และ ของเกิน (Extra)
        ควรเรียกใช้หลังจาก add found_inventories เสร็จแล้ว
        """
        # 1. หาสินค้าที่ 'ควรจะอยู่' ที่นี่ (System Expected)
        # คือสินค้าที่ current_location ล่าสุดเป็น Location นี้
        expected_items = Inventory.objects.filter(current_location=self.location)
        
        # 2. สินค้าที่ 'เจอจริง' (Scanned / Found)
        found_items = self.found_inventories.all()

        # แปลงเป็น Set เพื่อการคำนวณทางคณิตศาสตร์ (A - B)
        expected_ids = set(expected_items.values_list('id', flat=True))
        found_ids = set(found_items.values_list('id', flat=True))

        # ของหาย = ควรจะมี แต่ ไม่เจอ
        missing_ids = expected_ids - found_ids
        
        # ของเกิน (ย้ายมาโดยไม่ได้แจ้ง) = เจอ แต่ ระบบบอกว่าอยู่ที่อื่น
        extra_ids = found_ids - expected_ids

        # อัปเดตตัวเลขสรุป
        self.total_expected = len(expected_ids)
        self.total_found = len(found_ids)
        self.total_missing = len(missing_ids)
        self.save()

        # Update Location ล่าสุดของสินค้าที่เจอ (Real-time update)
        # สินค้าไหนที่เจอในรอบนี้ ให้ถือว่ามันอยู่ที่นี่แน่นอน
        Inventory.objects.filter(id__in=found_ids).update(
            current_location=self.location,
            last_seen_at=self.inspected_at
        )

        return {
            "missing_items": Inventory.objects.filter(id__in=missing_ids),
            "extra_items": Inventory.objects.filter(id__in=extra_ids)
        }    