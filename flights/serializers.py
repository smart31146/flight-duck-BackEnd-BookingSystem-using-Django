from rest_framework import serializers
from . import forms, models
from rest_framework.response import Response
from rest_framework import status


class AutoSuggestModelFormSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AutoSuggestModel
        fields = '__all__'

class BrowseRouteModelFormSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BrowseRouteModel
        fields = '__all__'

class FlightsLiveModelFormSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.FlightsLiveModel
        fields = '__all__'
        extra_kwargs = {
            'user_id' : {'required' : False} # define the 'user' field as 'read-only'
        }

class FlightsHotelPackageSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.FlightsHotelPackageModel
        fields = '__all__'
        extra_kwargs = {
            'user_id' : {'required' : False} # define the 'user' field as 'read-only'
        }