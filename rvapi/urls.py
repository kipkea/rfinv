app_name = "rvapi"

from django.urls import path, include
from rest_framework.routers import DefaultRouter
#from .views import RFIDTagViewAll,INV_Info, RFIDTagViewSet, LocationViewSet, ProductViewSet, InspectionViewSet

from .views import (
    InventoryListAPIView, InventoryDetailAPIView,
    InspectionListAPIView, InspectionDetailAPIView,
    # อย่าลืม import view ของ RFIDTag และ Location ด้วยถ้าทำเพิ่ม
)

urlpatterns = [
    # Inventory URLs
    path('api/inventory/', InventoryListAPIView.as_view(), name='inventory-list'),
    path('api/inventory/<int:pk>/', InventoryDetailAPIView.as_view(), name='inventory-detail'),

    # Inspection URLs
    path('api/inspections/', InspectionListAPIView.as_view(), name='inspection-list'),
    path('api/inspections/<int:pk>/', InspectionDetailAPIView.as_view(), name='inspection-detail'),
    
    # ... เพิ่ม path ของ Tags และ Location ตามต้องการ
]

'''
router = DefaultRouter()
router.register(r'rfidtags', RFIDTagViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'inventorys', ProductViewSet)
router.register(r'inspections', InspectionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('basic/', RFIDTagViewAll.as_view()),
    path('inv/<str:tagNo>/', INV_Info.as_view()),
    #path('basic/<str:id>/update/', rfinv_locView.as_view())  
]
'''  
    
  