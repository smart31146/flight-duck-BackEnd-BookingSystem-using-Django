from django.db import models
from django.core.validators import MaxValueValidator

class SearchPackageModel(models.Model):
    origin = models.CharField(max_length=10)
    destination = models.CharField(max_length=10)
    outbound_date = models.CharField(max_length=10)
    adults = models.IntegerField(default=0)
    children = models.IntegerField(default=0)
    country = models.CharField(max_length=10) # TODO: Figure out how this is supposed to work
    currency_format = models.CharField(max_length=10)
    locale = models.CharField(max_length=10)
    trip_days = models.IntegerField(default=1, validators=[MaxValueValidator(30)])
    destination_code = models.CharField(max_length=10, default='', blank=True)
    number_of_extended_months = models.IntegerField(default=0)
    user_id = models.CharField(max_length=100, blank=True)