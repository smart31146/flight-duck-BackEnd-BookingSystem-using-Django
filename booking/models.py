from django.db import models

class BookingModel(models.Model):
    room = models.CharField(max_length=255, default='')
    rate = models.FloatField(default=0)
    email = models.CharField(max_length=255, default='')
    phone = models.CharField(max_length=255, default='')
    fullname = models.CharField(max_length=255, default='')
    check_in = models.DateField(null=True)
    check_out = models.DateField(null=True)

# Create your models here.
