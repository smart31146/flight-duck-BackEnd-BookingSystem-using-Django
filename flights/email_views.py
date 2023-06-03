# email_views.py

from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from backend.settings import EMAIL_HOST_USER

@csrf_exempt
def post(request):
    data = json.loads(request.body)
    email_address = data['email_address']
    hotel_object = data['hotel_object']
    subject = 'Hotel Booking Confirmation'
    message = f'Dear {email_address},\n\nYour booking has been confirmed. Here are the details:\n\n{hotel_object}'
    email_from = EMAIL_HOST_USER
    recipient_list = [email_address, ]
    send_mail(subject, message, email_from, recipient_list)
    return JsonResponse({'message': 'Email sent successfully'})
