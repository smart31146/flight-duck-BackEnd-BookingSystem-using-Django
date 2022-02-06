# from rest_framework import routers
from django.urls import path, include, re_path
from . import views
# from rest_auth.registration.views import VerifyEmailView

# router = routers.DefaultRouter()
# router.register(r'', views.UserViewSet)

urlpatterns = [
    path('create/', views.CustomUserCreate.as_view(), name="create_user"),
    path('sample/', views.HelloWorld.as_view(), name="sample"),
    path('login/', views.signin, name='signin'),
    path('logout/<str:email>/', views.signout, name='signout'),
    path('chart/options', views.get_filter_options, name="chart-options"),
    path('chart/card_details/<int:year>/<int:month>', views.get_card_details, name="card_details"),
    path('chart/flight_origin_details/<int:year>/<int:month>', views.get_flight_origin_details, name="flight_origin_details"),
    path('chart/flight_destination_details/<int:year>/<int:month>', views.get_flight_destination_details, name="flight_destination_details"),
]
