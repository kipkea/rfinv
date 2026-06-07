from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.models import User
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers, serializers, viewsets
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rvapi import web_views


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
    # เพิ่มส่วนนี้ลงไปครับ
   generator_class=None,
   authentication_classes=[], # ปิด auth อื่นๆ สำหรับตัว schema เอง   
)



urlpatterns = [
    # Web MVT Routes
    path('web/login/', web_views.web_login, name='web_login'),
    path('web/logout/', web_views.web_logout, name='web_logout'),
    path('web/', web_views.dashboard, name='web_dashboard'),
    path('web/inventory/', web_views.inventory_list, name='web_inventory'),
    path('web/inspections/', web_views.inspection_history, name='web_inspection_history'),

    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    path('', include('rvapi.urls', namespace='rvapi')), 
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path(r"docs/", include_docs_urls(title="RFInv API")),   
    # เพิ่ม URL สำหรับ Swagger UI (ของ drf-yasg)
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'), 
]

# เพิ่มบรรทัดนี้ลงไป
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)