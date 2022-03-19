from email.policy import default
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator

class AutoSuggestModel(models.Model):
    query = models.CharField(max_length=100)

class BrowseRouteModel(models.Model):
    origin = models.CharField(max_length=10)
    destination = models.CharField(max_length=10)
    departureDate = models.CharField(max_length=100)
    returnDate = models.CharField(max_length=100, blank=True)
    currency_format = models.CharField(max_length=10)
    country = models.CharField(max_length=10)

class FlightsLiveModel(models.Model):
    originplace = models.CharField(max_length=10)
    destinationplace = models.CharField(max_length=10)
    outbounddate = models.CharField(max_length=100)
    inbounddate = models.CharField(max_length=100, blank=True)
    adults = models.IntegerField(default=0)
    children = models.IntegerField(default=0, blank=True)
    infants = models.IntegerField(default=0, blank=True)
    country = models.CharField(max_length=100)
    currency = models.CharField(max_length=100)
    locale = models.CharField(max_length=100)
    user_id = models.CharField(max_length=100, blank=True)

class LocaleModel(models.Model):
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=1000)

class CurrencyModel(models.Model):
    code = models.CharField(max_length=100)
    symbol = models.CharField(max_length=1000)
    thousands_separator = models.CharField(max_length=2)
    decimal_separator = models.CharField(max_length=2)
    symbol_on_left = models.BooleanField(default=True)
    space_between_amount_and_symbol = models.BooleanField(default=True)
    rounding_coefficient = models.IntegerField(default=0)
    decimal_digits = models.IntegerField(default=0)

class PackageModel(models.Model):
    origin = models.CharField(max_length=10)
    destination = models.CharField(max_length=10)
    outbound_date = models.CharField(max_length=10)
    adults = models.IntegerField(default=0)
    children = models.IntegerField(default=0)
    country = models.CharField(max_length=10) # TODO: Figure out how this is supposed to work
    currency_format = models.CharField(max_length=10)
    locale = models.CharField(max_length=10)
    destination_code = models.CharField(max_length=10, default='', blank=True)
    trip_days = models.IntegerField(default=1, validators=[MaxValueValidator(30)])
    number_of_extended_months = models.IntegerField(default=0)
    user_id = models.CharField(max_length=100, blank=True)

# TODO: Remove if redundant
class FlightsHotelPackageModel(models.Model):
    originplace = models.CharField(max_length=10)
    destinationplace = models.CharField(max_length=10)
    outbounddate = models.CharField(max_length=10,
        validators=[RegexValidator(regex='^.{10}$', message='Length has to be 10')])
    inbounddate = models.CharField(max_length=20)
    # inbounddate = models.CharField(max_length=10, blank=True,
    #     validators=[RegexValidator(regex='^.{10}$', message='Length has to be 10')])
    adults = models.IntegerField(default=0)
    rooms = models.IntegerField(default=0, validators=[MinValueValidator(1)])
    children = models.IntegerField(default=0, blank=True)
    infants = models.IntegerField(default=0, blank=True)
    country = models.CharField(max_length=10)
    currency_format = models.CharField(max_length=10)
    destination_code = models.CharField(max_length=10, default='', blank=True)
    locale = models.CharField(max_length=10)
    trip_days = models.IntegerField(default=1, blank=True, validators=[MaxValueValidator(30)])
    number_of_extended_months = models.IntegerField(default=0, blank=True, validators=[MaxValueValidator(2)])
    user_id = models.CharField(max_length=100, blank=True)

class CountryModel(models.Model):
    country_code = models.CharField(max_length=10)
    name = models.CharField(max_length=200)

class CityModel(models.Model):
    city_name = models.CharField(max_length=200, default='')
    city_code = models.CharField(max_length=20, unique=True, default='')

class AirportModel(models.Model):
    city = models.ForeignKey(CityModel, default='', 
        on_delete=models.CASCADE, null=True, blank=True)
    country = models.ForeignKey(CountryModel, default='', 
        on_delete=models.CASCADE, null=True, blank=True)
    airport_name = models.CharField(max_length=200)
    airport_code = models.CharField(max_length=20)

# class CountryAirportModel(models.Model):
#     country_code = models.ForeignKey(CountryModel, on_delete=models.CASCADE)
#     city_name = models.CharField(max_length=200)
#     # airport = models.ForeignKey(AirportModel, on_delete=models.CASCADE)
#     airport_name = models.CharField(max_length=200)
#     airport_code = models.CharField(max_length=20)
#     hotel_beds_code = models.CharField(max_length=20, default='')


