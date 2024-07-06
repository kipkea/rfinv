from rest_framework import serializers  
#from .models import rfinv_loc, rfinv_inv ,rfinv_check  
from .models import RFIDTag, Location, Inventory, Inspection
  
'''
class StudentSerializer(serializers.ModelSerializer):  
    first_name = serializers.CharField(max_length=200, required=True)  
    last_name = serializers.CharField(max_length=200, required=True)  
    address = serializers.CharField(max_length=200, required=True)  
    roll_number = serializers.IntegerField()  
    mobile = serializers.CharField(max_length=10, required=True)  
  
    class Meta:  
        model = Students  
        fields = ('__all__')  

'''  
'''class rfinv_loc(models.Model):
    Loc_ID = models.CharField(max_length=255,primary_key=True, editable=True, unique=True)
    Loc_Name = models.CharField(max_length=255, blank = True, null = True)
'''
class RFIDTag_SL(serializers.ModelSerializer):
    RFID = serializers.CharField(max_length=255, required=True)
    is_location = serializers.BooleanField(default=False)

    class Meta:
        model = RFIDTag
        fields = ('__all__')


class Location_SL(serializers.ModelSerializer):
    rfid_tag = RFIDTag_SL()

    class Meta:
        model = Location
        fields = '__all__'

class Inventory_SL(serializers.ModelSerializer):
    rfid_tag = RFIDTag_SL()

    class Meta:
        model = Inventory
        fields = '__all__'

class Inspection_SL(serializers.ModelSerializer):
    rfid_tags = RFIDTag_SL(many=True)

    class Meta:
        model = Inspection
        fields = '__all__'

'''
    def create(self, validated_data):  
        """ 
        Create and return a new `Students` instance, given the validated data. 
        """  
        return rfinv_loc.objects.create(**validated_data)  
  
    def update(self, instance, validated_data):  
        """ 
        Update and return an existing `Students` instance, given the validated data. 
        """  
        instance.Loc_ID = validated_data.get('Loc_ID', instance.Loc_ID)  
        instance.Loc_Name = validated_data.get('Loc_Name', instance.Loc_Name)  
  
        instance.save()  
        return instance  
'''
        
'''    
class rfinv_inv(models.Model):    
    Inv_ID = models.AutoField(primary_key=True, auto_created = True,editable=True, unique=True) 
    Inv_Name = models.CharField(max_length=255, blank = True, null = True)
    Inv_Created = models.DateTimeField(auto_now_add=True)
    Inv_Modified = models.DateTimeField(auto_now=True)
    RFCode = models.CharField(max_length=255, blank = True, null = True)
    
    #เอาไว้เก็บสถานที่เก็บสุดท้าย
    Inv_Last_Check_Time = models.DateTimeField(auto_now_add=True)
    Inv_Last_Loc = models.CharField(max_length=255, blank = True, null = True)
'''        
