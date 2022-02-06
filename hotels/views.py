from django.shortcuts import render
from stripe.api_resources import source
from . import models, serializers
from users import serializers as user_serializer
from users.models import NewUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
import hashlib
import time
import requests
import json
import traceback
from datetime import date
from django.db.models import Q
from django.forms.models import model_to_dict
from hotels import models as hotelModels
import stripe
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

HOTELS_API_URL = "https://api.test.hotelbeds.com"
HOTELS_API_KEY = "ce0f06ea4efa6d559dd869faae735266"
HOTELS_API_SECRET_KEY = "58a4678b4c"
# HOTELS_API_KEY = "0c62bbb9fee15426972a6169b4ed92e8"
# HOTELS_API_SECRET_KEY = "99d8ba99c8"
# HOTELS_API_KEY = "0d398a473d49170a9be6c9ac8c4a78ab"
# HOTELS_API_SECRET_KEY = "f1c803d58c"
HOTELS_PHOTOS_BASE_URL = "http://photos.hotelbeds.com/giata/bigger/"
STRIPE_SECRET_API_KEY = "sk_test_7YMuYhNOxeGvrecIvA8v8yB600369fxiZe"
STRIPE_SECRET_API_KEY = "sk_test_51IHEQ8IZl69pMaQiqvh0iaolEIVogZVCwtOPsb9tdfYpwbURXcgbcmpDygFi0vqTrv0pgw2MxbzgQWiDqStMuo7X00asuNhT5b"
# STRIPE_PUBLISHABLE_API_KEY = "pk_test_yyBiwHABM5W4vAzEiPij1w6p00gQZWAUUn"

def createXSignature():
    currentTimeStamp = int(time.time())
    result = HOTELS_API_KEY + HOTELS_API_SECRET_KEY + str(currentTimeStamp)
    result = hashlib.sha256(result.encode()).hexdigest()
    return result

def getHotelDetailsBasedOnCode(hotel):
    hotel_object = {}
    code = hotel['code']
    hotel_object['code'] = code
    hotel_details = models.HotelDetail.objects.filter(code=code).first()
    if hotel_details is not None:
        hotel_object['local'] = True
        hotel_details_dict = model_to_dict(hotel_details)
        hotel_object['hotel'] = hotel_details_dict['name']
        hotel_object['city'] = hotel_details_dict['city']
        hotel_object['latitude'] = hotel_details_dict['latitude']
        hotel_object['longitude'] = hotel_details_dict['longitude']
        hotel_object['description'] = hotel_details_dict['description']
        hotel_object['health_safety_code'] = hotel_details_dict['health_safety_code']

        facilities = models.HotelFacility.objects.filter(hotel__code=hotel_details_dict['code']).values().all()
        hotel_object['facilities'] = facilities

        hotel_category_details = models.HotelCategory.objects.filter(category_code=hotel_details_dict['category_code']).first()
        hotel_category_details_dict = model_to_dict(hotel_category_details)
        hotel_object['type'] = hotel_category_details_dict['accomodation_type']
        hotel_object['rating'] = hotel_category_details_dict['category_name']
        
        hotel_images = []
        images = models.HotelImage.objects.filter(hotel__code=code).all()
        if len(images)>0:
            hotel_images = [HOTELS_PHOTOS_BASE_URL + image['image_url'] for image in images.values('image_url')]
        hotel_object['images'] = hotel_images
    else:
        hotel_object['local'] = False
    return hotel_object

class LiveHotelsData:
    
    def __init__(self, hotelsData):
        self.hotelsData = hotelsData
    
    def processHotels(self):
        processedData = []

        if (self.hotelsData.get('hotels', None)):
            hotels = self.hotelsData['hotels'].get('hotels', None)
            # print("self hotels=====", self.hotelsData)
            # print("hotels=====", hotels)
            # print("hotels dictionary data=======", self.hotelsData['hotels'])
            if hotels:
                for hotel in hotels:
                    hotel_details = models.HotelDetail.objects.filter(code=hotel['code']).first()
                    if hotel_details is not None:
                        hotel_object = {}
                        hotel_object.update(getHotelDetailsBasedOnCode(hotel))
                        # print("hotel code =========", hotel, "\n")
                        try:
                            float(hotel_object['rating'].split(' ')[0])
                            hotel_object['rate'] = float(hotel['minRate'])
                            hotel_object['rooms'] = hotel['rooms']
                            processedData.append(hotel_object)
                        except:
                            print("exception hotel not found=====")
                            pass
                    else: 
                        print("hotel not found=====")
                    # print("hotel details not found=======for code ======= ", hotel['code'])
                    # print("hotels list============", processedData)

                    # hotel_object = {}
                    # hotel_object.update(getHotelDetailsBasedOnCode(hotel))
                    # hotel_object['rate'] = float(hotel['minRate'])
                    # hotel_object['rooms'] = hotel['rooms']
                    # processedData.append(hotel_object)
            
        # print("processedData=========", len(processedData))
        processedData.sort(key=lambda x: x['rate'], reverse=False)
        cheapestRate = 0
        if (len(processedData)>0):
            processedData[0]['cheapest'] = True
            cheapestRate = float(processedData[0]['rate'])
        for hotel in processedData:
            star_points = 0
            rating = float(hotel['rating'].split(' ')[0])
            ## within 25% of the cheapest hotel price range
            if hotel['rate']<=((0.25*cheapestRate)+cheapestRate):
                star_points = star_points+1
            # star points increase by 2, if rating is 5
            if rating == 5:
                star_points = star_points+2
            # star points increase by 1, if rating is greater than equal to 4
            if (rating >= 4) & (rating < 5):
                star_points = star_points+1
            hotel['star_points'] = star_points
        processedData.sort(key=lambda x: x['star_points'], reverse=False)
        processedData[0]['best_value'] = True

        return processedData

class SearchHotels(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        if user_id:
            userExists = NewUser.objects.filter(id=user_id).all()
            user = user_serializer.AddHotelSearchHistory(data = request.data)
            if user.is_valid():
                user.save()
            
            serializer = serializers.SearchHotelModelFormSerializer(data = request.data)
            if serializer.is_valid():
                liveHotelsPricingURL = HOTELS_API_URL + '/hotel-api/1.0/hotels'
                headers_dict = {
                    "Api-key": HOTELS_API_KEY,
                    "X-Signature": createXSignature(),
                    "Accept": "application/json",
                    "Accept-Encoding":"gzip",
                    "Content-Type": "application/json"
                }
                data = {
                    "stay": {
                        "checkIn": request.data['checkInDate'],
                        "checkOut": request.data['checkOutDate']
                    },
                    "occupancies": [
                        {
                            "rooms": request.data['rooms'],
                            "adults": request.data['adults'],
                            "children": request.data['children']
                        }
                    ],
                    # "destination": {
                    #     "code": request.data['destination']
                    # }
                    "hotels": {
                        "hotel": list(hotelModels.HotelDetail.objects.filter(destination_code=request.data['destination']).values_list('code', flat=True))
                    }
                }

                result = requests.post(
                    liveHotelsPricingURL,
                    json=data,
                    headers=headers_dict
                )
                # print("jsondata========", data)
                # print("hotel beds result===========", result.text)

                if (result.status_code == 200):
                    hotelsData = LiveHotelsData(json.loads(result.text)).processHotels()
                    return Response(hotelsData, status=status.HTTP_200_OK)
                else:
                    return Response({'message': 'Search query is invalid'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'No user id found'}, status=status.HTTP_406_NOT_ACCEPTABLE)

class UpdateCountry(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        getListofCountriesUrl = HOTELS_API_URL + '/hotel-content-api/1.0/locations/countries?fields=all&language=ENG'
        headers_dict = {
            "Api-key": HOTELS_API_KEY,
            "X-Signature": createXSignature(),
            "Accept": "application/json",
            "Accept-Encoding":"gzip",
            "Content-Type": "application/json"
        }

        result = requests.get(
            getListofCountriesUrl,
            headers=headers_dict
        )
        final_countries_list = []

        if (result.status_code == 200):
            json_result = json.loads(result.text)
            result_till_now = json_result['to']
            total_records = json_result['total']
            final_countries_list = json_result['countries']
            if (result_till_now != total_records):
                getListofCountriesUrl = HOTELS_API_URL + '/hotel-content-api/1.0/locations/countries?fields=all&language=ENG&from={}&to={}'.format(result_till_now+1, total_records)
                result = requests.get(
                    getListofCountriesUrl,
                    headers=headers_dict
                )
                json_result = json.loads(result.text)
                final_countries_list.extend(json_result['countries'])
                ### delete country and states data
                # models.HotelCountry.objects.all().delete()
                # models.HotelCountryState.objects.all().delete()
                for country in final_countries_list:
                    try:
                        country_object = models.HotelCountry.objects.create(
                            country_code = country['code'],
                            iso_code = country['isoCode'],
                            country_name = country['description']['content']
                        )
                        models.HotelCountryState.objects.bulk_create(
                            [models.HotelCountryState(**{
                                'state_code' : state['code'],
                                'state_name' : state['name'],
                                'country' : country_object})
                            for state in country['states']])
                    except:
                        pass

            return Response(
                {
                    'countries': final_countries_list,
                    'total': len(final_countries_list)
                }, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Search query is invalid'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateHotelCategory(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        models.HotelCategory.objects.all().delete()
        getListofCategoriesUrl = HOTELS_API_URL + '/hotel-content-api/1.0/types/categories?fields=all'
        headers_dict = {
            "Api-key": HOTELS_API_KEY,
            "X-Signature": createXSignature(),
            "Accept": "application/json",
            "Accept-Encoding":"gzip",
            "Content-Type": "application/json"
        }

        result = requests.get(
            getListofCategoriesUrl,
            headers=headers_dict
        )
        final_categories_list = []
        number_of_categories_saved = 0

        if (result.status_code == 200):
            json_result = json.loads(result.text)
            result_till_now = json_result['to']
            total_records = json_result['total']
            final_categories_list = json_result['categories']
            if (result_till_now != total_records):
                for category in final_categories_list:
                    try:
                        models.HotelCategory.objects.create(
                            category_code = category['code'],
                            accomodation_type = category['accommodationType'],
                            category_name = category['description']['content']
                        )
                        number_of_categories_saved = number_of_categories_saved+1
                    except:
                        pass

            return Response(
                {
                    'countries': final_categories_list,
                    'total': len(final_categories_list),
                    'saved': number_of_categories_saved
                }, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Search query is invalid'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateHotelFacility(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        models.HotelFacilityDetails.objects.all().delete()
        getListofFacilitiesUrl = HOTELS_API_URL + '/hotel-content-api/1.0/types/facilities?fields=all&language=ENG&from=1&to=800'
        headers_dict = {
            "Api-key": HOTELS_API_KEY,
            "X-Signature": createXSignature(),
            "Accept": "application/json",
            "Accept-Encoding":"gzip",
            "Content-Type": "application/json"
        }

        result = requests.get(
            getListofFacilitiesUrl,
            headers=headers_dict
        )
        final_facilities_list = []
        number_of_facilities_saved = 0

        if (result.status_code == 200):
            json_result = json.loads(result.text)
            result_till_now = json_result['to']
            total_records = json_result['total']
            final_facilities_list = json_result['facilities']
            if (result_till_now != total_records):
                for facility in final_facilities_list:
                    try:
                        models.HotelFacilityDetails.objects.create(
                            facility_code = facility['code'],
                            facility_group_code = facility['facilityGroupCode'],
                            facility_name = facility['description']['content']
                        )
                        number_of_facilities_saved = number_of_facilities_saved+1
                    except:
                        pass

            return Response(
                {
                    'facilities': final_facilities_list,
                    'total': len(final_facilities_list),
                    'saved': number_of_facilities_saved
                }, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Search query is invalid'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateHotel(APIView):
    permission_classes = [AllowAny]

    def getFacilityNameFromModel(self, facility):
        facility_name = models.HotelFacilityDetails.objects.filter(
            Q(facility_code=facility['facilityCode']) & 
            Q(facility_group_code=facility['facilityGroupCode'])
        ).values('facility_name').first()
        return facility_name['facility_name']

    # def getCategoryDetailsFromModel(self, category):
    #     self.distinct_categories = []
    #     values = models.HotelCategory.objects.filter(
    #         category_code=category
    #     ).values('accomodation_type').distinct()
    #     for categories in values:
    #         self.distinct_categories.append(categories['accomodation_type'])
    #     # return facility_name['facility_name']

    def get(self, request, *args, **kwargs):
        # delele all previous records
        models.HotelDetail.objects.all().delete()
        models.HotelRoom.objects.all().delete()
        models.HotelImage.objects.all().delete()
        models.HotelFacility.objects.all().delete()
  
        hotel_field_list = ",".join([
            'code', 'name', 'description', 'country', 'city', 
            'address', 'rooms', 'facilities', 'images', 
            'destinationCode', 'categoryCode', 'S2C', 'coordinates'])
        countries = models.HotelCountry.objects.all()
        # "IN", "AT", 'AU'
        # countries = models.HotelCountry.objects.filter(country_code__in=['IN']).all()
#         countries = models.HotelCountry.objects.filter(country_code__in=['AU']).all()
        # countries = models.HotelCountry.objects.filter(country_code__in=['IN', 'AU']).all()
        country_hotels_list = []
        for country in countries:
            getListofHotelsinCountryUrl = HOTELS_API_URL \
            + '/hotel-content-api/1.0/hotels?language=ENG&fields={}&countryCode={}&from=1&to=800'.format(hotel_field_list, country.country_code)
            headers_dict = {
                "Api-key": HOTELS_API_KEY,
                "X-Signature": createXSignature(),
                "Accept": "application/json",
                "Accept-Encoding":"gzip",
                "Content-Type": "application/json"
            }

            result = requests.get(
                getListofHotelsinCountryUrl,
                headers=headers_dict
            )
            
            if (result.status_code == 200):
                json_result = json.loads(result.text)
                result_till_now = json_result['to']
                total_records = json_result['total']
                final_hotels_list = json_result['hotels']
                if (result_till_now != total_records):
                    for record in range(result_till_now+1, total_records+1, 800):
                        getListofHotelsinCountryUrl = HOTELS_API_URL \
                            + '/hotel-content-api/1.0/hotels?fields=all&language=ENG&countryCode={}&from={}&to={}'.format(country.country_code, record, record+800)
                        headers_dict = {
                            "Api-key": HOTELS_API_KEY,
                            "X-Signature": createXSignature(),
                            "Accept": "application/json",
                            "Accept-Encoding":"gzip",
                            "Content-Type": "application/json"
                        }
                        result = requests.get(
                            getListofHotelsinCountryUrl,
                            headers=headers_dict
                        )
                        if (result.status_code != 200):
                            print()
                            print("url that broke======", getListofHotelsinCountryUrl)
                            print("broken=======", result.text)
                            break
                        else:
                            json_result = json.loads(result.text)
                            final_hotels_list.extend(json_result['hotels'])
                        
                country_hotels_dict = {}
                country_hotels_dict['country_name'] = country.country_name
                number_of_hotels_saved = 0
                number_of_hotels_not_saved = 0
                print("number of hotels found========", len(final_hotels_list), " for country====", country.country_name)
                
                for hotel in final_hotels_list:
                    try:
                        hotel_object = models.HotelDetail.objects.create(
                            code = hotel['code'],
                            name = hotel['name']['content'],
                            description = hotel['description']['content'] if hotel.get('description') else 'Sample Description',
                            city = hotel['city']['content'].strip(" "),
                            destination_code = hotel['destinationCode'],
                            category_code = hotel['categoryCode'],
                            health_safety_code = hotel['S2C'] if hotel.get('S2C') else '',
                            country = country,
                            latitude = hotel['coordinates']['latitude'],
                            longitude = hotel['coordinates']['longitude'],
                        )

                        models.HotelRoom.objects.bulk_create(
                            [models.HotelRoom(**{
                                'minPax' : room['minPax'],
                                'maxPax' : room['maxPax'],
                                'maxAdults' : room['maxAdults'],
                                'maxChildren' : room['maxChildren'],
                                'minAdults' : room['minAdults'],
                                'hotel' : hotel_object
                            })
                            for room in hotel['rooms']], ignore_conflicts=True)
                        
                        models.HotelFacility.objects.bulk_create(
                            [models.HotelFacility(**{
                                'facility_name' : self.getFacilityNameFromModel(facility),
                                'facility_chargeable': facility['indFee'] if facility.get('indFee') else False,
                                'facility_available': facility['indLogic'] if facility.get('indLogic') else False,
                                'facility_time_from' : facility['timeFrom'] if facility.get('timeFrom') else None,
                                'facility_time_to' : facility['timeTo'] if facility.get('timeTo') else None,
                                'hotel' : hotel_object
                            })
                            for facility in hotel['facilities']], ignore_conflicts=False)
                        
                        models.HotelImage.objects.bulk_create(
                            [models.HotelImage(**{
                                'image_url': image['path'] if image.get('path') else '',
                                'hotel' : hotel_object
                            })
                            for image in hotel['images']], ignore_conflicts=True)
                        number_of_hotels_saved = number_of_hotels_saved + 1
                    except Exception as e:
                        # print("exception ==========", e)
                        # print("traceback ==========", traceback.format_exc())
                        # # print("occurred in =========", hotel['code'])
                        # print("occurred in =========", hotel)
                        # print()
                        number_of_hotels_not_saved = number_of_hotels_not_saved + 1

                country_hotels_dict['hotels'] = len(final_hotels_list)
                country_hotels_dict['data_saved_for_hotels'] = number_of_hotels_saved
                country_hotels_dict['data_not_saved_for_hotels'] = number_of_hotels_not_saved
                country_hotels_list.append(country_hotels_dict)
            else:
                print("Exception in calling base url=========", result)
                return Response({'message': 'Search query is invalid'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            today = date.today()
            current_date = today.strftime("%Y-%m-%d")
            models.HotelBedsLastUpdate.objects.create(last_update = current_date)
        except Exception as e:
            print("last update date error======", e)
        return Response(
            {
                'status': country_hotels_list
            }, status=status.HTTP_200_OK)
        # else:
        #     return Response({'message': 'Search query is invalid'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SearchHotelContent(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        if user_id:
            userExists = NewUser.objects.filter(id=user_id).all()
            user = user_serializer.AddHotelSearchHistory(data = request.data)
            if user.is_valid():
                user.save()
            
            serializer = serializers.SearchHotelCountryWiseFormSerializer(data = request.data)
            if serializer.is_valid():
                liveHotelsPricingURL = HOTELS_API_URL + '/hotel-content-api/1.0/hotels/{}/details?language=ENG'
                headers_dict = {
                    "Api-key": HOTELS_API_KEY,
                    "X-Signature": createXSignature(),
                    "Accept": "application/json",
                    "Accept-Encoding":"gzip",
                    "Content-Type": "application/json"
                }
                data = {
                    "stay": {
                        "checkIn": request.data['checkInDate'],
                        "checkOut": request.data['checkOutDate']
                    },
                    "occupancies": [
                        {
                            "rooms": request.data['rooms'],
                            "adults": request.data['adults'],
                            "children": request.data['children']
                        }
                    ],
                    "destination": {
                        "code": request.data['destination']
                    }
                }

                result = requests.post(
                    liveHotelsPricingURL,
                    json=data,
                    headers=headers_dict
                )

                if (result.status_code == 200):
                    getFlightsData = LiveHotelsData(json.loads(result.text)).processHotels()
                    return Response(json.loads(result.text), status=status.HTTP_200_OK)
                else:
                    return Response({'message': 'Search query is invalid'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'No user id found'}, status=status.HTTP_406_NOT_ACCEPTABLE)


class BookableRateKey(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        checkRatesURL = HOTELS_API_URL \
            + '/hotel-api/1.0/checkrates'
        headers_dict = {
            "Api-key": HOTELS_API_KEY,
            "X-Signature": createXSignature(),
            "Accept": "application/json",
            "Accept-Encoding":"gzip",
            "Content-Type": "application/json"
        }
        rate_key_post = request.data['rate_key']

        data = {
            "rooms": [
                {
                    "rateKey": rate_key_post
                },
            ]
            # rate_key_post
        }
        # print("json data=======", data)

        result = requests.post(
            checkRatesURL,
            json=data,
            headers=headers_dict
        )
        # print("api result========", result.text)
        # print("api status========", result.status_code)
        
        if (result.status_code == 200):
            json_result = json.loads(result.text)
            # json_result = json_result['hotel']['rooms']
            # print("before sorting json_result========", json_result)
            # print()
            # json_result = sorted(json_result, key=lambda x: x['code'])
            # final_list = []
            # previous_code = json_result[0]['code']
            # final_list.append(json_result[0])
            # i = 0
            # for value in json_result[1:]:
            #     if previous_code == value['code']:
            #         final_list[i]['rates'].append(value['rates'][0])
            #     else:
            #         previous_code = value['code']
            #         final_list.append(value)
            #         i = i+1
                
            # print("after sorting json_result========", final_list)
            # print()
            try:
                rates = json_result['hotel']['rooms'][0]['rates'][0]
                net_amount = rates['net']
                rate_key = rates['rateKey']
                cancellationAmount = rates['cancellationPolicies'][0]['amount']            
                return Response(
                    {
                        'net': net_amount,
                        'cancellation_amount': cancellationAmount,
                        'rateKey': rate_key,
                    }, status.HTTP_200_OK
                )
            except Exception as e:
                # print("ratekey exception========", e)
                # print("json_result=========", json_result)
                # print()
                return Response(
                    {
                        'net': 0,
                        'cancellation_amount': 0,
                        'rateKey': rate_key_post,
                    }, status.HTTP_400_BAD_REQUEST
                )
            # return Response(
            #     # json_result,
            #     final_list,
            #     status.HTTP_200_OK
            # )
        else:
            return Response({'message': 'Rate key error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class HotelBookingEarlier(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        checkRatesURL = HOTELS_API_URL \
            + '/hotel-api/1.0/bookings'
        headers_dict = {
            "Api-key": HOTELS_API_KEY,
            "X-Signature": createXSignature(),
            "Accept": "application/json",
            "Accept-Encoding":"gzip",
            "Content-Type": "application/json"
        }
        holder_data = request.data['holder']
        rooms_information = request.data['rooms']

        data = {
            "holder": {
                "name": holder_data['name'],
                "surname": holder_data['surname']
            },
            "rooms": rooms_information,
            "clientReference": "FlightDuck",
            "remark": "Booking from website",
            "tolerance": 2
        }
        # print("json data=======", data)

        result = requests.post(
            checkRatesURL,
            json=data,
            headers=headers_dict
        )
        # print("api result========", result.text)
        # print("api status========", result.status_code)
        
        if (result.status_code == 200):
            json_result = json.loads(result.text)
            try:
                booking_reference = json_result['booking']['reference']
                booking_status = json_result['booking']['status']
                if booking_status == "CONFIRMED":
                    booking_status = True
                else:
                    booking_status = False
                models.HotelBookingModel.objects.create(
                    booking_reference = booking_reference,
                    booking_status = booking_status
                )
                return Response(
                    {
                        'reference': booking_reference,
                        'status': booking_status
                    }, status.HTTP_200_OK
                )
            except Exception as e:
                print("booking error=======", e)
                return Response(
                    {
                        'message': "Booking error check log"
                    }, status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response({
                'message': 'Rate key error'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class HotelBooking(APIView):
    permission_classes = [AllowAny]

    def fetchRateBasedOnRoomRateKey(self, room_rate_key):
        checkRatesURL = HOTELS_API_URL \
            + '/hotel-api/1.0/checkrates'
        headers_dict = {
            "Api-key": HOTELS_API_KEY,
            "X-Signature": createXSignature(),
            "Accept": "application/json",
            "Accept-Encoding":"gzip",
            "Content-Type": "application/json"
        }
        
        data = {
            "rooms": [
                {
                    "rateKey": room_rate_key
                },
            ]
        }

        result = requests.post(
            checkRatesURL,
            json=data,
            headers=headers_dict
        )
        if (result.status_code == 200):
            json_result = json.loads(result.text)
            try:
                rates = json_result['hotel']['rooms'][0]['rates'][0]
                net_amount = rates['net']
                return net_amount
            except Exception as e:
                print("ratekey exception========", e)
                return 0
        return 0

    def makeStripePayment(self, stripe_token, room_rate, adults, children):
        amount = 0
        currency = 'usd'
        
        amount = amount + (room_rate*adults)
        amount = amount + (room_rate*children)
        amount = int(amount*100)
        
        try:
            stripe.api_key = STRIPE_SECRET_API_KEY
            stripe.Charge.create(
                amount=amount,
                currency=currency,
                source=stripe_token,
                description='Hotel Booking payment',
                shipping={
                    'name':'Jenny Rosen',
                    'address': {
                        'line1': '510 Townsend St',
                        'postal_code': '98140',
                        'city': 'San Francisco',
                        'state': 'CA',
                        'country': 'US',
                    },
                },
            )
            return True
        except Exception as e:
            print("Exception stripe charge ======", e)
            return False

    def post(self, request, *args, **kwargs):
        # holder_data = request.data['holder']
        # rooms_information = request.data['rooms']
        stripe_token = request.data['stripeToken']
        rate_key = request.data['rateKey']
        adults = request.data['adults']
        children = request.data['children']
        users = request.data['users']
        new_user_data = []
        for user in users:
            details = {}
            details['name'] = user['name']
            details['surname'] = user['surname']
            details['type'] = user['personType']
            details['roomId'] = 1
            new_user_data.append(details)
        # print("new_user_data======", new_user_data)
        amount = float(self.fetchRateBasedOnRoomRateKey(rate_key))
        # print("amount of hotel booking ========", amount)
        stripe_payment_made = self.makeStripePayment(
            stripe_token, amount, adults, children)
        # print("stripe payment made=======", stripe_payment_made)
        if stripe_payment_made:
            # print("stripe payment made successfull ==========")
            checkRatesURL = HOTELS_API_URL \
                + '/hotel-api/1.0/bookings'
            headers_dict = {
                "Api-key": HOTELS_API_KEY,
                "X-Signature": createXSignature(),
                "Accept": "application/json",
                "Accept-Encoding":"gzip",
                "Content-Type": "application/json"
            }
            rooms = []
            rooms.append({
                'rateKey': rate_key,
                'paxes': new_user_data
            })
            # print("rooms array=====", rooms)

            data = {
                "holder": {
                    "name": new_user_data[0]['name'],
                    "surname": new_user_data[0]['surname']
                },
                "rooms": rooms,
                "clientReference": "FlightDuck",
                "remark": "Booking from website",
                "tolerance": 2
            }
            # print("json data=======", data)

            result = requests.post(
                checkRatesURL,
                json=data,
                headers=headers_dict
            )
            # print("api result========", result.text)
            # print("api status========", result.status_code)
            
            if (result.status_code == 200):
                json_result = json.loads(result.text)
                try:
                    booking_reference = json_result['booking']['reference']
                    booking_status = json_result['booking']['status']
                    if booking_status == "CONFIRMED":
                        booking_status = True
                    else:
                        booking_status = False
                    models.HotelBookingModel.objects.create(
                        booking_reference = booking_reference,
                        booking_status = booking_status
                    )
                    return Response(
                        {
                            'reference': booking_reference,
                            'status': booking_status
                        }, status.HTTP_200_OK
                    )
                except Exception as e:
                    print("booking error=======", e)
                    return Response(
                        {
                            'message': "Booking error check log"
                        }, status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response({
                    'message': 'Rate key error'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            print("stripe payment failed========")
            return Response({
                'message': 'Stripe payment error'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CreatePaymentIntent(APIView):
    permission_classes = [AllowAny]

    def fetchRateBasedOnRoomRateKey(self, room_rate_key):
        checkRatesURL = HOTELS_API_URL \
            + '/hotel-api/1.0/checkrates'
        headers_dict = {
            "Api-key": HOTELS_API_KEY,
            "X-Signature": createXSignature(),
            "Accept": "application/json",
            "Accept-Encoding":"gzip",
            "Content-Type": "application/json"
        }
        
        data = {
            "rooms": [
                {
                    "rateKey": room_rate_key
                },
            ]
        }

        result = requests.post(
            checkRatesURL,
            json=data,
            headers=headers_dict
        )
        if (result.status_code == 200):
            json_result = json.loads(result.text)
            try:
                rates = json_result['hotel']['rooms'][0]['rates'][0]
                net_amount = rates['net']
                return net_amount
            except Exception as e:
                print("ratekey exception========", e)
                return 0
        return 0

    def post(self, request, *args, **kwargs):
        amount = 0
        room_rate_key = request.data['rateKey']
        room_rate = float(self.fetchRateBasedOnRoomRateKey(room_rate_key))
        # print("room rate =====", room_rate)
        # currency = request.data['currency']
        currency = 'usd'
        
        # paxes = request.data['paxes']
        adults = request.data['adults']
        children = request.data['children']
        
        amount = amount + (room_rate*adults)
        amount = amount + (room_rate*children)
        amount = int(amount*100)
        # if children != 0:
            # if children%2 == 0:
            #     amount = amount + room_rate
            # else:
            #     amount = amount + 
            # for i in range(1, children+1, 2):
            #     if i%2 == 0:
            # count = children
            # while children:
            #     children = children%10
            #     pass

        
        try:
            stripe.api_key = STRIPE_SECRET_API_KEY
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                payment_method_types=["card"],
            )
            return Response({
                'intent': payment_intent
                }, status.HTTP_200_OK)
        except Exception as e:
            print("Exception stripe payment intent ======", e)
            print("request data=====", request.data)
            return Response({
                'intent': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ConfirmationMail(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        sender_email = "gurjas027@gmail.com"
        receiver_email = request.data['receiver_email']
        password = "Google@92G!"

        message = MIMEMultipart("alternative")
        message["Subject"] = "Hotel Booking Confirmation"
        message["From"] = sender_email
        message["To"] = receiver_email
        hotel_name = "MJ Grand Hotel"
        hotel_city = "Dehradun"
        booking_date = "26 Oct, 2021"
        booking_payment = "$ 35"

        text = """\
            Thank you for choosing Flight Duck services.
            Hotel - {0}, {1} has been booked for date {2} and payment of {3} has been received.
            
            Enjoy your stay.""".format(hotel_name, hotel_city, booking_date, booking_payment)
        
        html = """\
            <html>
            <body>
                <p>Thank you for choosing Flight Duck services.<br>
                Hotel - {0}, {1} has been booked for date {2} and payment of {3} has been received.<br>
                <br>
                Enjoy your stay.<br>
            </body>
            </html>
            """.format(hotel_name, hotel_city, booking_date, booking_payment)

        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        message.attach(part1)
        message.attach(part2)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, receiver_email, message.as_string()
            )
        return Response({
            'success': 'Mail sent'
            }, status.HTTP_200_OK)

        
