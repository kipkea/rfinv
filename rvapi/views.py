from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView  
from rest_framework.response import Response  
from rest_framework import status  
from .models import RFIDTag, Location, Inventory, Inspection
from .serializers import RFIDTag_SL, Location_SL, Inventory_SL , Inspection_SL
from django.shortcuts import get_object_or_404  
from rest_framework.permissions import IsAuthenticated
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework import viewsets, generics
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Q

class RFIDTagViewAll(APIView):  
    permission_classes = [ HasAPIKey | IsAuthenticated ]

    def get(self, request):    
        result = RFIDTag.objects.all()  
        serializers = RFIDTag_SL(result, many=True)  
        return Response({'status': 'success', "items":serializers.data}, status=200)  

class INV_Info(APIView):     
    permission_classes = [ HasAPIKey | IsAuthenticated ]

    def get(self, request, tagNo):    
        result = Inventory.objects.filter(rfid_tag__RFID=tagNo)
        serializers = Inventory_SL(result, many=True)  
        return Response({'status': 'success', "items":serializers.data}, status=200)  

class RFIDTagViewSet(viewsets.ModelViewSet):
    permission_classes = [ HasAPIKey | IsAuthenticated ]

    queryset = RFIDTag.objects.all()
    serializer_class = RFIDTag_SL

class LocationViewSet(viewsets.ModelViewSet):
    permission_classes = [ HasAPIKey | IsAuthenticated ]

    queryset = Location.objects.all()
    serializer_class = Location_SL

class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [ HasAPIKey | IsAuthenticated ]

    queryset = Inventory.objects.all()
    serializer_class = Inventory_SL


class InspectionViewSet(viewsets.ModelViewSet):
    permission_classes = [ HasAPIKey | IsAuthenticated ]
    
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