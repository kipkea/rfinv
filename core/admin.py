from django.contrib import admin

# Register your models here.

from .models import rfinv_loc,rfinv_inv,rfinv_check

"""
admin.site.register(rfinv_loc)
admin.site.register(rfinv_inv)
admin.site.register(rfinv_check)
"""
@admin.register(rfinv_loc)
class rfinv_locAdmin(admin.ModelAdmin):
    list_display = ('Loc_ID','Loc_Name')
    #list_filter = ('accType')
    #search_fields = ('accCode','accName')
    #prepopulated_fields = {'accName':('accCode')}
    #raw_id_fields=('accType')
    #date_hierarchy = ('CreateDate')
    #ordering = ('accCode')

@admin.register(rfinv_inv)
class rfinv_invAdmin(admin.ModelAdmin):
    list_display = ('Inv_ID','Loc_ID','Inv_Name','Inv_Last_Check_Time','Inv_Last_Loc')
    
@admin.register(rfinv_check)    
class rfinv_checkAdmin(admin.ModelAdmin):
    list_display = ('Chk_ID','Inv_ID','Loc_ID','Chk_Time')        
    
"""
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
    