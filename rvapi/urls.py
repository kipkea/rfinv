app_name = "rvapi"

from django.urls import path, include
from rest_framework.routers import DefaultRouter
#from .views import RFIDTagViewAll,INV_Info, RFIDTagViewSet, LocationViewSet, ProductViewSet, InspectionViewSet

from .views import (
    InventoryListAPIView, InventoryDetailAPIView,
    InspectionListAPIView, InspectionDetailAPIView,
    RFIDTagListAPIView, RFIDTagDetailAPIView,
    LocationListAPIView, LocationDetailAPIView,    
    InventoryImageDetailAPIView, InventoryImageListAPIView,
    # อย่าลืม import view ของ RFIDTag และ Location ด้วยถ้าทำเพิ่ม
    RFIDTagViewSet, 
    LocationViewSet, 
    InventoryViewSet, 
    InspectionViewSet,
    login_api,

)

# สร้าง Router และลงทะเบียน ViewSets
router = DefaultRouter()
router.register(r'rfid-tags', RFIDTagViewSet, basename='rfidtag')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'inspections', InspectionViewSet, basename='inspection')

urlpatterns = [
    # สำหรับ Login ด้วย Username/Password (Kivy จะส่ง POST มาที่นี่)
    path('api/login/', login_api, name='login_api'),
    
    # หากคุณใช้ SimpleJWT (จาก Error ก่อนหน้า) ต้องมี path สำหรับ Token ด้วย
    # path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

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
    
  