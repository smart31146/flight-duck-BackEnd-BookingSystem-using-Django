from django.urls import path
from . import views

urlpatterns = [
    path('package/', views.PackageSearch.as_view(), name="package-search"),
    path('flight/', views.FlightSearch.as_view(), name="flight-search"),
    path('hotel/', views.HotelSearch.as_view(), name="hotel-search"),
]