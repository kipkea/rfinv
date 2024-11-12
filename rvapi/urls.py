app_name = "rvapi"

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RFIDTagViewAll,INV_Info, RFIDTagViewSet, LocationViewSet, ProductViewSet, InspectionViewSet

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
  
    
  