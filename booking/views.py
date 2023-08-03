from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .models import BookingModel

class BookingView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        print( request.data)
        newbooking = BookingModel(room = request.data['room'], 
                                  rate = request.data['rate'],
                                  email = request.data['email'],
                                  phone = request.data['phone'],
                                  fullname = request.data['fullname'],
                                  check_in = request.data['check_in'],
                                  check_out = request.data['check_out']
                                  )
        newbooking.save()
        print(newbooking)
        return Response(
            {
                'message': 'success'
            }, status=status.HTTP_200_OK)

# Create your views here.
