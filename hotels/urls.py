from django.urls import path, include
from . import views

urlpatterns = [
    path('live-hotel-prices/', views.SearchHotels().as_view(), name="live-hotel-prices"),
    path('hotel-content-country/', views.SearchHotelContent().as_view(), name="hotel-content-country"),
    path('hotel-country/', views.UpdateCountry().as_view(), name="hotel-country"),
    path('hotel-categories/', views.UpdateHotelCategory().as_view(), name="hotel-categories"),
    path('hotel-facilities/', views.UpdateHotelFacility().as_view(), name="hotel-facilities"),
    path('update-country-hotels/', views.UpdateHotel().as_view(), name="update-country-hotels"),
    path('fetch-bookable-rate-key/', views.BookableRateKey().as_view(), name="update-country-hotels"),
    path('hotel-booking/', views.HotelBooking().as_view(), name="hotel-booking"),
    path('create-payment-intent/', views.CreatePaymentIntent().as_view(), name="create-payment-intent"),
    path('confirmation-mail/', views.ConfirmationMail.as_view(), name="confirmation-mail"),
]