from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView  
from rest_framework.response import Response  
from rest_framework import status  
from .models import rfinv_loc  
from .serializers import rfinv_locSL
from django.shortcuts import get_object_or_404  
from rest_framework.permissions import IsAuthenticated
from rest_framework_api_key.permissions import HasAPIKey





# Create your views here.  
class rfinv_locViewAll(APIView):  
    permission_classes = [ HasAPIKey | IsAuthenticated ]

    def get(self, request):    
        result = rfinv_loc.objects.all()  
        serializers = rfinv_locSL(result, many=True)  
        return Response({'status': 'success', "items":serializers.data}, status=200)  
      
class rfinv_locView(APIView):  
    permission_classes = [ HasAPIKey | IsAuthenticated ]

    def get(self, request, id):    
        result = rfinv_loc.objects.get(Loc_ID=id)        
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