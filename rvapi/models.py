from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

'''
class Product(models.Model):
    class Status(models.IntegerChoices):
        ACTIVE = 1, "Active"
        INACTIVE = 2, "Inactive"
        ARCHIVED = 3, "Archived"

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.PositiveSmallIntegerField(choices=Status.choices)

    def __str__(self):
        return self.name
'''


          
    
class RFIDTag(models.Model):
    RFID = models.CharField(max_length=100, unique=True)
    is_location = models.BooleanField(default=False)

    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        #db_table = "RFIDTag"
        ordering = ('RFID',)        
        
    def __str__(self):
        return self.RFID

class Location(models.Model):
    rfid_tag = models.OneToOneField(RFIDTag, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank = True, null = True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        #db_table = "Location"
        ordering = ('rfid_tag',)        

    def __str__(self):
        return self.name
    
class Inventory(models.Model): #res
    rfid_tag = models.OneToOneField(RFIDTag, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    #เอาไว้เก็บสถานที่เก็บสุดท้าย
    Inv_Last_Check_Time = models.DateTimeField(auto_now_add=True, blank = True, null = True)
    Inv_Last_Loc = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank = True,)

    class Meta:
        #db_table = ('Inventory',)
        ordering = ('rfid_tag',)        

    def __str__(self):
        return self.name
 
class InventoryImage(models.Model):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='inventory_images/%Y/%m/%d/')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    photographed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    photographed_at = models.DateTimeField(default=timezone.now)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="GPS Latitude")
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, help_text="GPS Longitude")

    class Meta:
        ordering = ['-photographed_at']

    def __str__(self):
        return f"Image for {self.inventory.name} taken at {self.photographed_at.strftime('%Y-%m-%d')}"

'''
class Inspection(models.Model):  #staff
    #rfid_tags = models.ManyToManyField(RFIDTag)
    Ins_invs = models.ManyToManyField(Inventory, related_name='InvTags')
    inspected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    inspected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        #db_table = ('Inspection',)
        ordering = ('inspected_at',)   
        
    def save(self, *args, **kwargs):
        location_count = self.Ins_invs.Inventory.rfid_tag.filter(is_location=True).count()
        if location_count > 1:
            raise ValueError("Multiple locations in one inspection are not allowed.")
        super(Inspection,self).save(*args, **kwargs)
        
    def __str__(self):
        return f"Inspection on {self.inspected_at} by {self.inspected_by}"    
'''

class Inspection(models.Model):
    """
    บันทึกการตรวจสอบสินทรัพย์ ณ สถานที่และเวลาที่กำหนด
    """
    # ระบุสถานที่ที่ทำการตรวจสอบอย่างชัดเจน ป้องกันการลบสถานที่หากมีการอ้างอิงถึง
    location = models.ForeignKey(Location, on_delete=models.PROTECT, help_text="สถานที่ที่ทำการตรวจสอบ")

    # รายการสินทรัพย์ทั้งหมดที่พบในการตรวจสอบครั้งนี้
    inspected_inventories = models.ManyToManyField(Inventory, related_name='inspections', blank=True)

    # ผู้ที่ทำการตรวจสอบ
    inspected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # วันที่และเวลาที่ตรวจสอบ (ใช้ default=timezone.now เพื่อให้สามารถแก้ไขย้อนหลังได้)
    inspected_at = models.DateTimeField(default=timezone.now)

    class Meta:
        # เรียงลำดับจากรายการล่าสุดไปเก่าสุด
        ordering = ('-inspected_at',)

    def __str__(self):
        location_name = self.location.name if self.location else "N/A"
        return f"Inspection at {location_name} on {self.inspected_at.strftime('%Y-%m-%d')}"
    
    # หมายเหตุ: การอัปเดตสถานะของ Inventory (Inv_Last_Loc, Inv_Last_Check_Time)
    # ควรจัดการในส่วนของ View หรือ Form หลังจากที่บันทึก Inspection และ
    # ข้อมูล `inspected_inventories` เรียบร้อยแล้ว เพื่อความถูกต้องของข้อมูล
    #
    # ตัวอย่างการทำงานใน View:
    # inspection = form.save()
    # for inv in inspection.inspected_inventories.all():
    #     inv.Inv_Last_Loc = inspection.location
    #     inv.Inv_Last_Check_Time = inspection.inspected_at
    #     inv.save()