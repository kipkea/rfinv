from django.db import models
from django.contrib.auth.models import User

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
    
class Inventory(models.Model):
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

'''
class InspectionTag(models.Model):
    inspection = models.ForeignKey('Inspection', on_delete=models.CASCADE)
    rfid_tag = models.ForeignKey(RFIDTag, on_delete=models.CASCADE)
    inspected_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        db_table = ('InspectionTag',)

    def __str__(self):
        return f"{self.rfid_tag.rfid} - {self.inspected_at}"
'''   

class Inspection(models.Model):
    rfid_tags = models.ManyToManyField(RFIDTag)
    #rfid_tags = models.ManyToManyField(RFIDTag, through='InspectionTag')
    inspected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    inspected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        #db_table = ('Inspection',)
        ordering = ('inspected_at',)   
        
    def save(self, *args, **kwargs):
        location_count = self.rfid_tags.filter(is_location=True).count()
        if location_count > 1:
            raise ValueError("Multiple locations in one inspection are not allowed.")
        super(Inspection,self).save(*args, **kwargs)
        
    def __str__(self):
        return f"Inspection on {self.inspected_at} by {self.inspected_by}"    

