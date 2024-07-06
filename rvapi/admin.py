from django.contrib import admin

# Register your models here.

from .models import RFIDTag, Location, Inventory, Inspection

"""
admin.site.register(rfinv_loc)
admin.site.register(rfinv_inv)
admin.site.register(rfinv_check)
"""
@admin.register(RFIDTag)
class RFIDTagAdmin(admin.ModelAdmin):
    list_display = ('RFID','is_location')
    #list_filter = ('accType')
    #search_fields = ('accCode','accName')
    #prepopulated_fields = {'accName':('accCode')}
    #raw_id_fields=('accType')
    #date_hierarchy = ('CreateDate')
    #ordering = ('accCode')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('rfid_tag','name','recorded_by','recorded_at',)
    
@admin.register(Inventory)    
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('rfid_tag','name','recorded_by','recorded_at','Inv_Last_Check_Time','Inv_Last_Loc',)
    
admin.site.register(Inspection)

"""
class rfinv_loc(models.Model):
    Loc_ID = models.CharField(max_length=255,primary_key=True, editable=True, unique=True)
    Loc_Name = models.CharField(max_length=255, blank = True, null = True)
    
    class Meta:
        ordering = ('Loc_ID',)
        
    def __str__(self):
        return str(self.Loc_ID)  + " : " + str(self.Loc_Name)
    
class rfinv_inv(models.Model):
    Inv_ID = models.AutoField(primary_key=True, auto_created = True,editable=True, unique=True) 
    Inv_Name = models.CharField(max_length=255, blank = True, null = True)
    Inv_Created = models.DateTimeField(auto_now_add=True)
    Inv_Modified = models.DateTimeField(auto_now=True)
    RFCode = models.CharField(max_length=255, blank = True, null = True)
    
    #เอาไว้เก็บสถานที่เก็บสุดท้าย
    Inv_Last_Check_Time = models.DateTimeField(auto_now_add=True)
    Inv_Last_Loc = models.CharField(max_length=255, blank = True, null = True)
   
    class Meta:
        ordering = ('Inv_ID',)
        
    def __str__(self):
        return str(self.Inv_ID)  + " : " + str(self.Inv_Name)
    
class rfinv_check(models.Model):
    Chk_ID = models.AutoField(primary_key=True, editable=True, auto_created = True, unique=True)
    Inv_ID = models.ForeignKey(rfinv_inv, on_delete=models.CASCADE, related_name='Chk_Inv') 
    Loc_ID = models.ForeignKey(rfinv_loc, on_delete=models.CASCADE, related_name='Chk_Location') 
    Chk_Time = models.DateTimeField(auto_now_add=True)
    

@admin.register(tbAccount)
class tbAccountAdmin(admin.ModelAdmin):
    list_display = ('accCode','accName','accType')
    #list_filter = ('accType')
    #search_fields = ('accCode','accName')
    #prepopulated_fields = {'accName':('accCode')}
    #raw_id_fields=('accType')
    #date_hierarchy = ('CreateDate')
    #ordering = ('accCode')

@admin.register(tbProject)
class tbProjectAdmin(admin.ModelAdmin):
    list_display = ('prjID','prjType','prjG1','prjG2','prjG3','prjDesc','prjYear','prjBudget')

@admin.register(tbAccMatch)
class tbAccMatchAdmin(admin.ModelAdmin):
    #list_display = ('amID','accCode','prjID','amDesc')
    list_display = ('prjID',)

@admin.register(tbProject_Transaction)
class tbProject_TransactionAdmin(admin.ModelAdmin):
    list_display = ('trID','amID','trDesc','tnsDate','tnsAmount','tnsType')
"""    
    