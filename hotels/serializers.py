from rest_framework import serializers
from . import models
from rest_framework.response import Response
from rest_framework import status

class SearchHotelModelFormSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.SearchHotelModel
        fields = '__all__'
        extra_kwargs = {
            'user_id' : {'required' : False} # define the 'user' field as 'read-only'
        }

class SearchHotelCountryWiseFormSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.SearchHotelCountryWiseModel
        fields = '__all__'
