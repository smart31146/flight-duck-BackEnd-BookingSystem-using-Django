from django.contrib import admin
from .models import NewUser, UserFlightsSearchModel, UserHotelSearchModel, FlightsHotelPackageModel
from django.contrib.auth.admin import UserAdmin
from django.forms import TextInput, Textarea, CharField
from django import forms
from django.db import models
from import_export.admin import ImportExportModelAdmin

# class UserAdminConfig(ImportExportModelAdmin, UserAdmin):
class UserAdminConfig(UserAdmin):
    # class Meta:
    #     model = NewUser
    model = NewUser
    
    list_display = ('email', 'first_name',
                    'is_active', 'is_staff')
    fieldsets = (
        ('User Details', {'fields': ('email', 'first_name', 'last_name')}),
    )
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 20, 'cols': 60})},
    }
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name')}
         ),
    )
    search_fields = ('email', 'first_name',)
    ordering = ('-start_date',)

class UserFlightsSearchModelAdmin(admin.ModelAdmin):
    model = UserFlightsSearchModel
    
    list_display = ('originplace', 'destinationplace', 'country')
    list_filter = ('country', 'destinationplace', 'outbounddate', 'inbounddate')
    
    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

class FlightsHotelPackageModelAdmin(admin.ModelAdmin):
    model = FlightsHotelPackageModel

    list_display = ('originplace', 'destinationplace', 'country')
    list_filter = ('country', 'destinationplace', 'outbounddate', 'inbounddate')

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False
    
admin.site.register(NewUser, UserAdminConfig)
admin.site.register(UserFlightsSearchModel, UserFlightsSearchModelAdmin)
admin.site.register(FlightsHotelPackageModel, FlightsHotelPackageModelAdmin)