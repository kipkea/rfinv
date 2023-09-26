from django.db import models

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

class rfinv_loc(models.Model):
    Loc_ID = models.CharField(max_length=255,primary_key=True, editable=True, unique=True)
    Loc_Name = models.CharField(max_length=255, blank = True, null = True)
    
    class Meta:
        ordering = ('Loc_ID',)
        
    def __str__(self):
        return str(self.Loc_ID)  + " : " + str(self.Loc_Name)
    
class rfinv_inv(models.Model):
    Inv_ID = models.CharField(max_length=255,primary_key=True, editable=True, unique=True)
    Loc_ID = models.ForeignKey(rfinv_loc, on_delete=models.CASCADE, related_name='InvLocationID') 
    Inv_Name = models.CharField(max_length=255, blank = True, null = True)
    Inv_Last_Check_Time = models.DateTimeField(auto_now_add=True)
    Inv_Last_Loc = models.CharField(max_length=255, blank = True, null = True)
    
    class Meta:
        ordering = ('Inv_ID',)
        
    def __str__(self):
        return str(self.Inv_ID)  + " : " + str(self.Inv_Name)
    
class rfinv_check(models.Model):
    Chk_ID = models.AutoField(primary_key=True, editable=True, auto_created = True, unique=True)
    Inv_ID = models.ForeignKey(rfinv_inv, on_delete=models.CASCADE, related_name='ChkInventoryID') 
    Loc_ID = models.ForeignKey(rfinv_loc, on_delete=models.CASCADE, related_name='ChkLocationID') 
    Chk_Time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('Chk_ID',)
        
    def __str__(self):
        return str(self.Chk_ID)  
            
    
class Person(models.Model):
    name = models.CharField(max_length=100, verbose_name="full name")