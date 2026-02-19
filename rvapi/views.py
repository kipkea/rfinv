from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView  
from rest_framework.response import Response  
from rest_framework import status  
from .models import RFIDTag, Location, Inventory, Inspection, UserAPIKey
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



from .serializers import (
    RFIDTagSerializer, LocationSerializer, InventorySerializer, 
    InspectionSerializer, InspectionCreateSerializer
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
                "user_id": user.id
            }, status=200)
        except UserAPIKey.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Invalid API Key"}, status=401)

    # --- กรณีที่ 2: ใช้ Username/Password ---
    elif username and password:
        user = authenticate(username=username, password=password)
        if user is not None:
            print(f"User {username} authenticated successfully with username/password.")
            return JsonResponse({
                "status": "success",
                "message": f"Welcome {user.username}",
                "user_id": user.id
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
        serializer.save(registered_by=self.request.user)

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all().prefetch_related('evidence_images')
    serializer_class = InventorySerializer

    def perform_create(self, serializer):
        serializer.save(registered_by=self.request.user)

class InspectionViewSet(viewsets.ModelViewSet):
    queryset = Inspection.objects.all()
    serializer_class = InspectionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # บันทึกข้อมูลพื้นฐานก่อน
        inspection = serializer.save(inspected_by=self.request.user)
        
        # เรียก Celery Task ให้ทำงานเบื้องหลัง
        process_inspection_results.delay(inspection.id)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "Inspection started. Processing results in background.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
# --- 1. ตัวอย่างแบบ CRUD ปกติ (Inventory) ---

class InventoryListAPIView(APIView):
    permission_classes = [ HasAPIKey | IsAuthenticatedOrReadOnly | AllowAny]
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
    permission_classes = [ HasAPIKey | IsAuthenticatedOrReadOnly]
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

    def delete(self, request, pk):
        inventory = self.get_object(pk)
        inventory.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- 2. ตัวอย่างแบบ Logic ซับซ้อน (Inspection / ตรวจนับ) ---

class InspectionListAPIView(APIView):
    permission_classes = [ HasAPIKey | IsAuthenticatedOrReadOnly]
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
    permission_classes = [ HasAPIKey | IsAuthenticatedOrReadOnly]
    
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
        missing_items = Inventory.objects.filter(
            Q(rfid_tag__is_location=False) & 
            ~Q(rfid_tag__inspection__inspected_at__gte=threshold_date)
        ).distinct()
        serializer = Inventory_SL(missing_items, many=True)
        return Response(serializer.data)
'''   
     
         
'''
class LocationView(APIView):  
    permission_classes = [ HasAPIKey | IsAuthenticated ]

    def get(self, request, id):    
        result = Location.objects.get(Loc_ID=id)        
        if id:  
            serializers = rfinv_locSL(result)  
            return Response({'success': 'success', "items":serializers.data}, status=200)  
        
        result = rfinv_loc.objects.all()  
        serializers = rfinv_locSL(result, many=True)  
        return Response({'status': 'success', "items":serializers.data}, status=200)  
  
    def post(self, request):  
        serializer = rfinv_locSL(data=request.data)  
        if serializer.is_valid():  
            serializer.save()  
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)  
        else:  
            return Response({"status": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)  
  
    def patch(self, request, id):  
        result = rfinv_loc.objects.get(Loc_ID=id)  
        serializer = rfinv_locSL(result, data = request.data, partial=True)  
        if serializer.is_valid():  
            serializer.save()  
            return Response({"status": "success", "data": serializer.data})  
        else:  
            return Response({"status": "error", "data": serializer.errors})  
  
    def delete(self, request, Loc_ID=None):  
        result = get_object_or_404(rfinv_loc, Loc_ID=id)  
        result.delete()  
        return Response({"status": "success", "data": "Record Deleted"})
'''        