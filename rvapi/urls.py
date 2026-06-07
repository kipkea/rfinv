app_name = "rvapi"

from django.urls import path, include
#from rest_framework.routers import DefaultRouter
from .views_report import (report_dashboard, generate_location_report, generate_product_report, 
                           generate_inspection_pdf, generate_disposed_report)

from .views import (
    InventoryListAPIView, InventoryDetailAPIView,
    InspectionListAPIView, InspectionDetailAPIView,
    RFIDTagListAPIView, RFIDTagDetailAPIView,
    LocationListAPIView, LocationDetailAPIView,    
    InventoryImageDetailAPIView, InventoryImageListAPIView,
    login_api,
    dispose_inventory_api
)


urlpatterns = [
    # สำหรับ Login ด้วย Username/Password (Kivy จะส่ง POST มาที่นี่)
    path('api/login/', login_api, name='login_api'),
    
    # InventoryImages URLs
    path('api/InventoryImages/', InventoryImageListAPIView.as_view(), name='inventoryimage-list'),
    path('api/InventoryImages/<int:pk>/', InventoryImageDetailAPIView.as_view(), name='inventoryimage-detail'),
  
    # Locations URLs
    path('api/Locations/', LocationListAPIView.as_view(), name='location-list'),
    path('api/Locations/<int:pk>/', LocationDetailAPIView.as_view(), name='location-detail'),
    
    # RFIDTags URLs
    path('api/RFIDTags/', RFIDTagListAPIView.as_view(), name='rfidtag-list'),
    path('api/RFIDTags/<int:pk>/', RFIDTagDetailAPIView.as_view(), name='rfidtag-detail'),
    
    # Inventory URLs
    path('api/inventory/', InventoryListAPIView.as_view(), name='inventory-list'),
    path('api/inventory/<int:pk>/', InventoryDetailAPIView.as_view(), name='inventory-detail'),

    # Inspection URLs
    path('api/inspections/', InspectionListAPIView.as_view(), name='inspection-list'),
    path('api/inspections/<int:pk>/', InspectionDetailAPIView.as_view(), name='inspection-detail'),
    
    path('reports/', report_dashboard, name='report_dashboard'),
    path('reports/location/pdf/', generate_location_report, name='generate_location_report'),
    path('reports/product/pdf/', generate_product_report, name='generate_product_report'),    
    path('reports/inspection/<int:pk>/pdf/', generate_inspection_pdf, name='generate_inspection_pdf'),
    path('reports/disposed/pdf/', generate_disposed_report, name='generate_disposed_report'),
    path('api/inventory/<int:pk>/dispose/', dispose_inventory_api, name='dispose_inventory_api'),
]


    
  