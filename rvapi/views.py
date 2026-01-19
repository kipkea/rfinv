from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView  
from rest_framework.response import Response  
from rest_framework import status  
from .models import RFIDTag, Location, Inventory, Inspection
#from .serializers import RFIDTag_SL, Location_SL, Inventory_SL , Inspection_SL
from django.shortcuts import get_object_or_404  
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework import viewsets, generics
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Q

from .serializers import (
    RFIDTagSerializer, LocationSerializer, InventorySerializer, 
    InspectionSerializer, InspectionCreateSerializer
)

# --- 1. ตัวอย่างแบบ CRUD ปกติ (Inventory) ---

class InventoryListAPIView(APIView):
    permission_classes = [ HasAPIKey | IsAuthenticatedOrReadOnly]
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