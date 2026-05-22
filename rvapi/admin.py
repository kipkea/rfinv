from django.contrib import admin

# Register your models here.
from .models import RFIDTag, Location, Inventory, InventoryImage, Inspection, UserAPIKey

@admin.register(RFIDTag)
class RFIDTagAdmin(admin.ModelAdmin):
    list_display = ('rfid_code', 'is_location', 'registered_by', 'registered_at')
    search_fields = ('rfid_code',)
    list_filter = ('is_location',)    


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'rfid_tag', 'created_by', 'created_at')
    search_fields = ('name',)
        
@admin.register(Inventory)    
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'rfid_tag', 
        'current_location', 
        'last_seen_at', 
        'registered_by'
    )
    search_fields = ('name', 'rfid_tag__rfid_code')
    list_filter = ('current_location',)
    
@admin.register(InventoryImage)
class InventoryImageAdmin(admin.ModelAdmin):
    list_display = ('inventory', 'photographed_at', 'photographed_by')

@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = (
        'location', 
        'inspected_at', 
        'inspected_by', 
        'total_expected', 
        'total_found', 
        'total_missing'
    )
    list_filter = ('location', 'inspected_at')     

@admin.register(UserAPIKey)
class UserAPIKeyAdmin(admin.ModelAdmin):
    list_display = ['user', 'key', 'created_at']
    readonly_fields = ['key'] # ป้องกันการแก้ไข Key ด้วยมือ
      
