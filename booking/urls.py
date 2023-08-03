from django.urls import path, include
from . import views

urlpatterns = [
    path('add', views.BookingView.as_view(), name="add_booking"),
]