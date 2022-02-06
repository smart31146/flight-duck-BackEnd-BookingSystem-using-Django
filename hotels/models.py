from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
# from django.contrib.gis.db import models as geoModel

class SearchHotelModel(models.Model):
    destination = models.CharField(max_length=10)
    checkInDate = models.CharField(max_length=10,
        validators=[RegexValidator(regex='^.{10}$', message='Length has to be 10')])
    checkOutDate = models.CharField(max_length=10,
        validators=[RegexValidator(regex='^.{10}$', message='Length has to be 10')])
    rooms = models.IntegerField(default=0, validators=[MinValueValidator(1)])
    adults = models.IntegerField(default=0, validators=[MinValueValidator(1)])
    children = models.IntegerField(default=0, blank=True)
    user_id = models.CharField(max_length=10, blank=True)

class SearchHotelCountryWiseModel(models.Model):
    country_iso_code = models.CharField(max_length=60)

class HotelBedsLastUpdate(models.Model):
    last_update = models.DateTimeField()

class HotelCategory(models.Model):
    category_code = models.CharField(max_length=20, unique=True)
    accomodation_type = models.CharField(max_length=100, unique=False)
    category_name = models.CharField(max_length=20, unique=False)

class HotelFacilityDetails(models.Model):
    facility_code = models.IntegerField()
    facility_group_code = models.IntegerField()
    facility_name = models.CharField(max_length=300)
    
    
class HotelCountry(models.Model):
    country_code = models.CharField(max_length=20, unique=True)
    iso_code = models.CharField(max_length=20, unique=False)
    country_name = models.CharField(max_length=20, unique=False)

class HotelCountryState(models.Model):
    state_code = models.CharField(max_length=20)
    state_name = models.CharField(max_length=20)
    country = models.ForeignKey(HotelCountry, on_delete=models.CASCADE)
    
class HotelDestinations(models.Model):
    code = models.CharField(max_length=20)
    iso_code = models.CharField(max_length=20)
    # country_code = models.CharField(max_length=20)
    country = models.ForeignKey(HotelCountry, on_delete=models.CASCADE)
    
class HotelDetail(models.Model):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=900)
    city = models.CharField(max_length=200, default='')
    country = models.ForeignKey(HotelCountry, on_delete=models.CASCADE)
    destination_code = models.CharField(max_length=10, default='')
    category_code = models.CharField(max_length=10, default='')
    health_safety_code = models.CharField(max_length=10, default='')
    latitude = models.DecimalField(max_digits=20, decimal_places=3, default=0)
    longitude = models.DecimalField(max_digits=20, decimal_places=3, default=0)

class HotelFacility(models.Model):
    facility_name = models.CharField(max_length=300)
    facility_chargeable = models.BooleanField(default=False, blank=True)
    facility_available = models.BooleanField(default=False, blank=True)
    facility_time_from = models.TimeField(blank=True, null=True)
    facility_time_to = models.TimeField(blank=True, null=True)
    hotel = models.ForeignKey(HotelDetail, default='', on_delete=models.CASCADE, blank=True)

class HotelImage(models.Model):
    image_url = models.CharField(max_length=1000)
    hotel = models.ForeignKey(HotelDetail, default='', on_delete=models.CASCADE, blank=True)

class HotelRoom(models.Model):
    minPax = models.IntegerField()
    maxPax = models.IntegerField()
    maxAdults = models.IntegerField()
    maxChildren = models.IntegerField()
    minAdults = models.IntegerField()
    hotel = models.ForeignKey(HotelDetail, default='', on_delete=models.CASCADE, blank=True)

class HotelBookingModel(models.Model):
    booking_date = models.DateTimeField(auto_now=True)
    booking_reference = models.CharField(max_length=50)
    booking_status = models.BooleanField()










