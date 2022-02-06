from rest_framework import serializers
# from .models import NewUser
from . import models
from flights.models import FlightsLiveModel


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Currently unused in preference of the below.
    """
    email = serializers.EmailField(required=True)
    # username = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    password = serializers.CharField(min_length=8, write_only=True)

    class Meta:
        model = models.NewUser
        fields = ('email', 'first_name', 'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        # as long as the fields are the same, we can just use this
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

class AddFlightSearchHistory(serializers.ModelSerializer):

    class Meta:
        model = models.UserFlightsSearchModel
        fields = '__all__'

class AddHotelSearchHistory(serializers.ModelSerializer):

    class Meta:
        model = models.UserHotelSearchModel
        fields = '__all__'

class AddFlightsHotelPackageHistory(serializers.ModelSerializer):

    class Meta:
        model = models.FlightsHotelPackageModel
        fields = '__all__'
        