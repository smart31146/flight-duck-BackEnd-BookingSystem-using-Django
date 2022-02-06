from .models import NewUser, UserFlightsSearchModel, \
    UserHotelSearchModel, FlightsHotelPackageModel
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, logout
import random
import re
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, F, Sum, Avg, Q
from django.db.models.functions import ExtractYear, ExtractMonth
from utils.charts import months, colorPrimary, colorSuccess, colorDanger, generate_color_palette, get_year_dict


def generate_session_token(length=10):
    return ''.join(random.SystemRandom().choice([chr(i) for i in range(97, 123)] + [str(i) for i in range(10)]) for _ in range(length))


@csrf_exempt
def signin(request, backend='django.contrib.auth.backends.ModelBackend'):
    if not request.method == 'POST':
        return JsonResponse({'error': 'Provide email and password for the user'})
    
    username = request.POST['email']
    password = request.POST['password']

    if not re.match("^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$", username):
        return JsonResponse({'error': 'Enter a valid email'})

    if len(password) < 3:
        return JsonResponse({'error': 'Password needs to be at least of 8 characters'})

    UserModel = get_user_model()

    try:
        user = UserModel.objects.get(email=username)

        if user.check_password(password):
            usr_dict = UserModel.objects.filter(
                email=username).values().first()
            usr_dict.pop('password')

            token = generate_session_token()
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return JsonResponse({
                'id': usr_dict['id'],
                'first_name': usr_dict['first_name'], 
                'last_name': usr_dict['last_name'], 
                'email': usr_dict['email'],
                })
        else:
            return JsonResponse({'error': 'Invalid password'})

    except UserModel.DoesNotExist:
        return JsonResponse({'error': 'No user with email exists.'})


def signout(request, email):
    logout(request)

    UserModel = get_user_model()

    try:
        # user = UserModel.objects.get(pk=id)
        # user.session_token = "0"
        # user.save()
        UserModel.objects.get(email=email)

    except UserModel.DoesNotExist:
        return JsonResponse({'error': 'Invalid user email'})

    return JsonResponse({'success': 'Logout success'})


from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import CustomUserSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated


class CustomUserCreate(APIView):
    permission_classes = (AllowAny, )

    def post(self, request, format='json'):
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                if user:
                    json = serializer.data
                    return Response(json, status=status.HTTP_201_CREATED)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except:
                return JsonResponse({'error': 'User already registed with this email address'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HelloWorld(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        content = {'message': 'Hello, World!'}
        return Response(content)

@staff_member_required
def get_filter_options(request):
    users = NewUser.objects.annotate(year=ExtractYear('created_at')).values('year').order_by('-year').distinct()
    years = [user['year'] for user in users]
    months = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    return JsonResponse({
        'years': years,
        'months': months
    })

@staff_member_required
def get_card_details(request, year, month):
    flights = UserFlightsSearchModel.objects.filter(\
        Q(created_at__year=year) & Q(created_at__month=month))\
        .annotate(month=ExtractMonth('created_at'), 
        year=ExtractYear('created_at'))\
        .values('year', 'month').count()

    hotels = UserHotelSearchModel.objects.filter(\
        Q(created_at__year=year) & Q(created_at__month=month))\
        .annotate(month=ExtractMonth('created_at'), 
        year=ExtractYear('created_at'))\
        .values('year', 'month').count()
    
    flights_hotel_package = FlightsHotelPackageModel.objects.filter(\
        Q(created_at__year=year) & Q(created_at__month=month))\
        .annotate(month=ExtractMonth('created_at'), 
        year=ExtractYear('created_at'))\
        .values('year', 'month').count()
    
    new_users = NewUser.objects.filter(\
        Q(created_at__year=year) & Q(created_at__month=month))\
        .annotate(month=ExtractMonth('created_at'), 
        year=ExtractYear('created_at'))\
        .values('email', 'year', 'month').distinct().count()
    
    return JsonResponse({
        'new_users': new_users,
        'flights': flights,
        'hotels': hotels,
        'flight-hotel-package': flights_hotel_package,
    })

@staff_member_required
def get_flight_origin_details(request, year, month):
    flights = UserFlightsSearchModel.objects.filter(\
        Q(created_at__year=year) & Q(created_at__month=month))\
        .annotate(month=ExtractMonth('created_at'), 
        year=ExtractYear('created_at'))\
        .values('year', 'month', 'originplace', 'destinationplace')
    
    unique_origin_dict = dict()
    unique_origin = flights.values('originplace').annotate(Count('id'))
    for origin in unique_origin:
        unique_origin_dict[origin['originplace']] = origin['id__count'] 
    
    return JsonResponse({
        'title': 'Flight searches for origin',
        'data': {
            'labels': list(unique_origin_dict.keys()),
            'datasets': [{
                'label': 'Number of counts',
                'backgroundColor': generate_color_palette(len(unique_origin_dict)),
                'borderColor': generate_color_palette(len(unique_origin_dict)),
                'data': list(unique_origin_dict.values()),
            }]
        },
    })

@staff_member_required
def get_flight_destination_details(request, year, month):
    flights = UserFlightsSearchModel.objects.filter(\
        Q(created_at__year=year) & Q(created_at__month=month))\
        .annotate(month=ExtractMonth('created_at'), 
        year=ExtractYear('created_at'))\
        .values('year', 'month', 'destinationplace')
    
    unique_destination_dict = dict()
    unique_destination = flights.values('destinationplace').annotate(Count('id'))
    for destination in unique_destination:
        unique_destination_dict[destination['destinationplace']] = destination['id__count'] 
    
    return JsonResponse({
        'title': 'Flight searches for destination',
        'data': {
            'labels': list(unique_destination_dict.keys()),
            'datasets': [{
                'label': 'Number of counts',
                'backgroundColor': generate_color_palette(len(unique_destination_dict)),
                'borderColor': generate_color_palette(len(unique_destination_dict)),
                'data': list(unique_destination_dict.values()),
            }]
        },
    })
