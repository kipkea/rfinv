from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView  
from rest_framework.response import Response  
from rest_framework import status  
from .models import RFIDTag, Location, Inventory, Inspection, UserAPIKey, InventoryImage, User
#from .serializers import RFIDTag_SL, Location_SL, Inventory_SL , Inspection_SL
from django.shortcuts import get_object_or_404  
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.permissions import AllowAny
from rest_framework import viewsets, generics
from rest_framework.decorators import action, authentication_classes
from django.utils import timezone
from django.db.models import Q

from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from .authentication import APIKeyAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from drf_yasg.utils import swagger_auto_schema



from .serializers import (
    RFIDTagSerializer, LocationSerializer, InventorySerializer, 
    InspectionSerializer, InspectionCreateSerializer, InventoryImageSerializer, UserSerializer
)

           
@api_view(['GET'])
@authentication_classes([APIKeyAuthentication, JWTAuthentication]) # รองรับทั้ง 2 แบบ
@permission_classes([IsAuthenticated])
def get_inventory_data(request):
    # ถึงจุดนี้ request.user จะถูกเซตให้โดยอัตโนมัติ ไม่ว่าจะมาด้วยวิธีไหน
    data = {"item": "Sensor Node A", "owner": request.user.username}
    return Response(data)


@api_view(['POST'])
@permission_classes([AllowAny]) # สำคัญมาก: อนุญาตให้ใครก็ได้เข้าถึงหน้า Login
@csrf_exempt
def login_api(request):
    # 1. ตรวจสอบว่าเป็นการ Login แบบไหน (ดูจากข้อมูลที่ส่งมา)
    api_key = request.data.get('api_key')    
    username = request.data.get('username')
    password = request.data.get('password')
    
    # --- กรณีที่ 1: ใช้ API Key ---
    if api_key:
        try:
            key_obj = UserAPIKey.objects.get(key=api_key)
            user = key_obj.user
            print(f"User {user.username} authenticated successfully with API Key.")
            return JsonResponse({
                "status": "success",
                "message": f"Welcome {user.username} (Authenticated via API Key)",
                "user_id": user.id,
                "user_name": user.username
            }, status=200)
        except UserAPIKey.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Invalid API Key"}, status=401)

    # --- กรณีที่ 2: ใช้ Username/Password ---
    elif username and password:
        user = authenticate(username=username, password=password)
        if user is not None:
            print(f"User {username} authenticated successfully with username/password.")
            # ค้นหาหรือสร้าง API Key เพื่อส่งกลับให้แอปพลิเคชันใช้ยืนยันตัวตน
            api_key_obj = UserAPIKey.objects.filter(user=user).first()
            if not api_key_obj:
                api_key_obj = UserAPIKey.objects.create(user=user)
            return JsonResponse({
                "status": "success",
                "message": f"Welcome {user.username}",
                "user_id": user.id,
                "user_name": user.username,
                "key": api_key_obj.key
            }, status=200)
        else:
            return JsonResponse({"status": "error", "message": "Invalid Credentials"}, status=401)

    # --- กรณีข้อมูลไม่ครบ ---
    print("Login attempt failed: No credentials provided.")
    return JsonResponse({"status": "error", "message": "Please provide Credentials or API Key"}, status=400)
        
class RFIDTagViewSet(viewsets.ModelViewSet):
    queryset = RFIDTag.objects.all()
    serializer_class = RFIDTagSerializer

    def perform_create(self, serializer):
        # เช็คก่อนว่ามี User ล็อกอินใน Request หรือไม่
        if self.request.user and self.request.user.is_authenticated:
            serializer.save(registered_by=self.request.user)
        else:
            serializer.save()

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

    def perform_create(self, serializer):
        # บันทึกข้อมูลและระบุตัวผู้สร้าง (ป้องกัน Error AnonymousUser)
        if self.request.user and self.request.user.is_authenticated:
            location = serializer.save(created_by=self.request.user)
        else:
            location = serializer.save()
            
class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all().prefetch_related('evidence_images')
    serializer_class = InventorySerializer

    def perform_create(self, serializer):
        # เช็คก่อนว่ามี User ล็อกอินใน Request หรือไม่
        if self.request.user and self.request.user.is_authenticated:
            serializer.save(registered_by=self.request.user)
        else:
            serializer.save()

class InspectionViewSet(viewsets.ModelViewSet):
    queryset = Inspection.objects.all()
    serializer_class = InspectionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # บันทึกข้อมูลพื้นฐานก่อน
        # ป้องกัน Error AnonymousUser เมื่อเชื่อมต่อผ่าน API Key
        if self.request.user and self.request.user.is_authenticated:
            inspection = serializer.save(inspected_by=self.request.user)
        else:
            inspection = serializer.save()
        
        # เรียก Celery Task ให้ทำงานเบื้องหลัง
        process_inspection_results.delay(inspection.id)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "Inspection started. Processing results in background.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    

# --- 1. ตัวอย่างแบบ CRUD ปกติ (InventoryImage) ---

class InventoryImageListAPIView(APIView):
    authentication_classes = [APIKeyAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly | AllowAny]
    """
    รองรับ:
    - GET: ดึงรายการTagทั้งหมด (รองรับ ?location_id=...)
    - POST: สร้างTagใหม่
    """
    def get(self, request):
        InventoryImages = InventoryImage.objects.all()
           
        serializer = InventoryImageSerializer(InventoryImages, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = InventoryImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class InventoryImageDetailAPIView(APIView):
    authentication_classes = [APIKeyAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    """
    รองรับ: GET (ดู), PUT (แก้), DELETE (ลบ) รายตัว
    """
    def get_object(self, pk):
        return get_object_or_404(InventoryImage, pk=pk)

    def get(self, request, pk):
        InventoryImages = self.get_object(pk)
        serializer = InventoryImageSerializer(InventoryImages)
        return Response(serializer.data)

    def put(self, request, pk):
        InventoryImages = self.get_object(pk)
        serializer = InventoryImageSerializer(InventoryImages, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        InventoryImages = self.get_object(pk)
        InventoryImages.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
# --- 1. ตัวอย่างแบบ CRUD ปกติ (Location) ---

class LocationListAPIView(APIView):
    authentication_classes = [APIKeyAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly | AllowAny]
    """
    รองรับ:
    - GET: ดึงรายการTagทั้งหมด (รองรับ ?location_id=...)
    - POST: สร้างTagใหม่
    """
    def get(self, request):
        Locations = Location.objects.all()
           
        serializer = LocationSerializer(Locations, many=True)
        return Response(serializer.data)


    def post(self, request):
        serializer = LocationSerializer(data=request.data)
        if serializer.is_valid():
            # บันทึกข้อมูลและระบุตัวผู้สร้าง (ป้องกัน Error AnonymousUser)
            if request.user and request.user.is_authenticated:
                location = serializer.save(created_by=request.user)
            else:
                location = serializer.save()
                
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LocationDetailAPIView(APIView):
    authentication_classes = [APIKeyAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    """
    รองรับ: GET (ดู), PUT (แก้), DELETE (ลบ) รายตัว
    """
    def get_object(self, pk):
        return get_object_or_404(Location, pk=pk)

    def get(self, request, pk):
        Locations = self.get_object(pk)
        serializer = LocationSerializer(Locations)
        return Response(serializer.data)

    def put(self, request, pk):
        Locations = self.get_object(pk)
        serializer = LocationSerializer(Locations, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        Locations = self.get_object(pk)
        serializer = LocationSerializer(Locations, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        Locations = self.get_object(pk)
        Locations.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

# --- 1. ตัวอย่างแบบ CRUD ปกติ (RFIDTag) ---

class RFIDTagListAPIView(APIView):
    authentication_classes = [APIKeyAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly | AllowAny]
    """
    รองรับ:
    - GET: ดึงรายการTagทั้งหมด (รองรับ ?location_id=...)
    - POST: สร้างTagใหม่
    """
    def get(self, request):
        queryset = RFIDTag.objects.all()
        
        # 1. กรองข้อมูลว่าต้องการ Tag ของ Inventory (false) หรือ Location (true)
        is_location = request.query_params.get('is_location')
        if is_location is not None:
            is_loc_bool = str(is_location).lower() in ['true', '1', 't', 'y', 'yes']
            queryset = queryset.filter(is_location=is_loc_bool)
            
        # 2. กรองเฉพาะ RFID Tag ที่ยังไม่ถูกผูกกับสินค้าชิ้นอื่น (is_used=false)
        is_used = request.query_params.get('is_used')
        if is_used is not None and str(is_used).lower() in ['false', '0', 'n', 'no']:
            queryset = queryset.filter(inventory_profile__isnull=True)
           
        serializer = RFIDTagSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = RFIDTagSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class RFIDTagDetailAPIView(APIView):
    authentication_classes = [APIKeyAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    """
    รองรับ: GET (ดู), PUT (แก้), DELETE (ลบ) รายตัว
    """
    def get_object(self, pk):
        return get_object_or_404(RFIDTag, pk=pk)

    def get(self, request, pk):
        RFIDTags = self.get_object(pk)
        serializer = RFIDTagSerializer(RFIDTags)
        return Response(serializer.data)

    def put(self, request, pk):
        RFIDTags = self.get_object(pk)
        serializer = RFIDTagSerializer(RFIDTags, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        RFIDTags = self.get_object(pk)
        serializer = RFIDTagSerializer(RFIDTags, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        RFIDTags = self.get_object(pk)
        RFIDTags.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
# --- 1. ตัวอย่างแบบ CRUD ปกติ (Inventory) ---

class InventoryListAPIView(APIView):
    authentication_classes = [APIKeyAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly | AllowAny]
    """
    รองรับ:
    - GET: ดึงรายการสินค้าทั้งหมด (รองรับ ?location_id=...)
    - POST: สร้างสินค้าใหม่
    """
    def get(self, request):
        inventories = Inventory.objects.all()
        
        # Manual Filter: กรองตาม Location
        location_id = request.query_params.get('location_id')
        if location_id:
            inventories = inventories.filter(current_location_id=location_id)
            
        serializer = InventorySerializer(inventories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = InventorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InventoryDetailAPIView(APIView):
    authentication_classes = [APIKeyAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    """
    รองรับ: GET (ดู), PUT (แก้), DELETE (ลบ) รายตัว
    """
    def get_object(self, pk):
        return get_object_or_404(Inventory, pk=pk)

    def get(self, request, pk):
        inventory = self.get_object(pk)
        serializer = InventorySerializer(inventory)
        return Response(serializer.data)

    def put(self, request, pk):
        inventory = self.get_object(pk)
        serializer = InventorySerializer(inventory, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        inventory = self.get_object(pk)
        serializer = InventorySerializer(inventory, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        inventory = self.get_object(pk)
        inventory.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- 2. ตัวอย่างแบบ Logic ซับซ้อน (Inspection / ตรวจนับ) ---

class InspectionListAPIView(APIView):
    authentication_classes = [APIKeyAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get(self, request):
        """ดูประวัติการตรวจสอบทั้งหมด"""
        inspections = Inspection.objects.all()
        serializer = InspectionSerializer(inspections, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Logic สำคัญ: รับค่า RFID มาสแกน -> คำนวณของหาย -> ตอบกลับทันที
        """
        # ใช้ CreateSerializer ที่รับ scanned_rfid_codes
        serializer = InspectionCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # save() จะไปเรียก create() ใน serializer ที่เราเขียน Logic คำนวณไว้
            inspection = serializer.save() 

            # ดึงผลลัพธ์ที่คำนวณเสร็จแล้ว (จาก _temp_results ที่ฝากไว้ใน object)
            results = getattr(inspection, '_temp_results', {})

            # เตรียมข้อมูลตอบกลับ (Custom Response)
            missing_serialized = InventorySerializer(results.get('missing_items', []), many=True).data
            extra_serialized = InventorySerializer(results.get('extra_items', []), many=True).data

            response_data = {
                "inspection_id": inspection.id,
                "status": "completed",
                "summary": {
                    "total_expected": inspection.total_expected,
                    "total_found": inspection.total_found,
                    "total_missing": inspection.total_missing
                },
                "missing_items": missing_serialized,
                "extra_items": extra_serialized
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InspectionDetailAPIView(APIView):
    authentication_classes = [APIKeyAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request, pk):
        """ดูรายละเอียดการตรวจสอบรายครั้ง"""
        inspection = get_object_or_404(Inspection, pk=pk)
        serializer = InspectionSerializer(inspection)
        return Response(serializer.data)

# (คุณสามารถทำ RFIDTagListAPIView และ LocationListAPIView ในลักษณะเดียวกับ Inventory ได้เลยครับ)



'''
###ก่อนแก้ไข
class RFIDTagViewAll(APIView):  
    permission_classes = [ HasAPIKey | IsAuthenticatedOrReadOnly]

    def get(self, request):    
        print("Request Headers:", request.headers) 
        result = RFIDTag.objects.all()  
        serializers = RFIDTag_SL(result, many=True)  
        return Response({'status': 'success', "items":serializers.data}, status=200)  

class INV_Info(APIView):     
    permission_classes = [ HasAPIKey | IsAuthenticatedOrReadOnly ]

    def get(self, request, tagNo):    
        result = Inventory.objects.filter(rfid_tag__RFID=tagNo)
        serializers = Inventory_SL(result, many=True)  
        return Response({'status': 'success', "items":serializers.data}, status=200)  

class RFIDTagViewSet(viewsets.ModelViewSet):
    permission_classes = [ HasAPIKey | IsAuthenticatedOrReadOnly ]

    queryset = RFIDTag.objects.all()
    serializer_class = RFIDTag_SL

class LocationViewSet(viewsets.ModelViewSet):
    permission_classes = [ HasAPIKey | IsAuthenticatedOrReadOnly ]

    queryset = Location.objects.all()
    serializer_class = Location_SL

class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [ HasAPIKey | IsAuthenticatedOrReadOnly ]

    queryset = Inventory.objects.all()
    serializer_class = Inventory_SL


class InspectionViewSet(viewsets.ModelViewSet):
    permission_classes = [ HasAPIKey | IsAuthenticatedOrReadOnly ]
    
    queryset = Inspection.objects.all()
    serializer_class = Inspection_SL

    @action(detail=False, methods=['get'])
    def missing_items(self, request):
        threshold_date = timezone.now() - timezone.timedelta(days=30)
        #print(threshold_date)
        missing_items = I
'''