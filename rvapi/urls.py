app_name = "rvapi"

from .views import rfinv_locView  
from django.urls import path  
  
urlpatterns = [
    path('basic/', rfinv_locView.as_view()),
    path('basic/<str:id>/', rfinv_locView.as_view()),
    path('basic/<str:id>/update/', rfinv_locView.as_view())  
]
  
    
  