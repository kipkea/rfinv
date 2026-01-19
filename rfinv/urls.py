"""
URL configuration for rfinv project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin

from django.urls import path, include
from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets
#from core.views import PersonListView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']

# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)



#from rest_framework_swagger.views import get_swagger_view
from rest_framework.documentation import include_docs_urls
#schema_view = get_swagger_view(title="RFInv API")

# ตั้งค่า Schema View
schema_view = get_schema_view(
   openapi.Info(
      title="RFID Inventory API",
      default_version='v1',
      description="API สำหรับระบบตรวจสอบสินค้าคงคลังด้วย RFID",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    #path('api/', include('rvapi.urls', namespace='rvapi')),
    path('', include('rvapi.urls', namespace='rvapi')), 
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    #path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    #path(r"swagger-docs/", schema_view),
    path(r"docs/", include_docs_urls(title="RFInv API")),   
    # เพิ่ม URL สำหรับ Swagger UI (ของ drf-yasg)
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'), 
]

