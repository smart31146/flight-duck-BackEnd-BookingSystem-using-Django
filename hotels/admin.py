from django.contrib import admin
from .models import HotelCountry, HotelBookingModel

class HotelCountryAdmin(admin.ModelAdmin):

    list_display = ('country_code', 'country_name')

class HotelBookingModelAdmin(admin.ModelAdmin):

    list_display = ('booking_date', 'booking_reference', 'booking_status')

admin.site.register(HotelCountry, HotelCountryAdmin)
admin.site.register(HotelBookingModel, HotelBookingModelAdmin)