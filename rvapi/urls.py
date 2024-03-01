app_name = "rvapi"

from .views import rfinv_locView, rfinv_locViewAll
from django.urls import path  
  
urlpatterns = [
    path('basic/', rfinv_locViewAll.as_view()),
    path('basic/<str:id>/', rfinv_locView.as_view()),
    path('basic/<str:id>/update/', rfinv_locView.as_view())  
]
  
    
  