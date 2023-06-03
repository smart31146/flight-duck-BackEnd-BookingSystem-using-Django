from django.urls import path, include
from . import views

urlpatterns = [
    path('autosuggest/', views.AutoSuggest.as_view(), name="autosuggest"),
    path('browse-routes/', views.BrowseRoutes.as_view(), name="browse-routes"),
    path('live-flight-prices/', views.FlightLivePrices().as_view(), name="live-flight-prices"),
    path('store-locale/', views.storeLocaleInformation, name="store-locale"),
    path('store-currency/', views.storeCurrenciesInformation, name="store-currency"),
    path('cache-flight-hotels-package/', views.CacheFlightHotelsPackage.as_view(), name="cache-flight-hotels-package"),
    path('get-countries/', views.GetCountries.as_view(), name="get-countries"),
    path('get-airport-code/', views.GetAirportCode.as_view(), name="get-airport-code"),
]