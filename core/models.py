from django.db import models

# Create your models here.

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
            
    
    