from django.shortcuts import render
import json, requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . import forms, models, serializers
from users import serializers as user_serializer
from users.models import NewUser
from hotels import models as hotelModels
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
import datetime
import hashlib
import time
import requests
import json
import random
from calendar import monthrange
from django.forms.models import model_to_dict
from django.db.models import Q
from hotels import views as hotels_view
from hotels.views import getHotelDetailsBasedOnCode
import traceback
import sys
from .services import package_service
from backend import settings
import numpy as np
import pandas as pd
import codecs
from pprint import pprint
from datetime import timedelta
import io
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from backend.settings import EMAIL_HOST_USER

HOTELS_API_URL = "https://api.test.hotelbeds.com"
HOTELS_API_KEY = "ce0f06ea4efa6d559dd869faae735266"
HOTELS_API_SECRET_KEY = "58a4678b4c"
# HOTELS_API_KEY = "0c62bbb9fee15426972a6169b4ed92e8"
# HOTELS_API_SECRET_KEY = "99d8ba99c8"
# HOTELS_API_KEY = "0d398a473d49170a9be6c9ac8c4a78ab"
# HOTELS_API_SECRET_KEY = "f1c803d58c"
HOTELS_PHOTOS_BASE_URL = "http://photos.hotelbeds.com/giata/bigger/"

FLIGHTS_API_URL = "https://partners.api.skyscanner.net/apiservices/"
# FLIGHTS_API_KEY = "prtl6749387986743898559646983194"
FLIGHTS_API_KEY = "fl687154418168043982723635787130"


def createXSignature():
    currentTimeStamp = int(time.time())
    result = HOTELS_API_KEY + HOTELS_API_SECRET_KEY + str(currentTimeStamp)
    result = hashlib.sha256(result.encode()).hexdigest()
    return result


class AutoSuggest(APIView):
    permission_classes = [AllowAny]

def post(self, request, format='json'):
    # TODO change this endpoint for local based on country
    print("in autosuiggest")
    flights_destination_auto_suggestion = '{0}autosuggest/v3/geo/hierarchy/flights/en-AU'.format(FLIGHTS_API_URL)

    serializer = serializers.AutoSuggestModelFormSerializer(data=request.data)
    if serializer.is_valid():
        query = serializer.data['query']
        headers = {'apiKey': FLIGHTS_API_KEY}
        result = requests.get(flights_destination_auto_suggestion, params={'query': query}, headers=headers)

        if result.status_code == 200:
            response_data = json.loads(result.text)
            places_map = response_data['placesMap']
            # Filter out airports that do not serve commercial flights
            filtered_places = {k: v for k, v in places_map.items() if not (v['type'] == 'airport' and v['commercial'] == False)}
            # Flatten the response data
            flat_response = []
            for _, place in filtered_places.items():
                flat_response.append(place)
            return Response(flat_response, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class OfflineFlightsData:

    def __init__(self, flightsData):
        self.flightsData = flightsData

    def getDestination(self, id):
        for place in self.flightsData['Places']:
            if place['PlaceId'] == id:
                name = place['Name']
                city = place['CityName']
                country = place['CountryName']
                return name, city, country

    def getOrigin(self, id):
        for place in self.flightsData['Places']:
            if place['PlaceId'] == id:
                name = place['Name']
                city = place['CityName']
                country = place['CountryName']
                return name, city, country

    def getCarrier(self, carriersId):
        carriersNames = []
        for carrier in self.flightsData['Carriers']:
            for id in carriersId:
                if carrier['CarrierId'] == id:
                    carriersNames.append(carrier['Name'])
        return carriersNames

    def processFlights(self):
        processedData = []

        print(self.flightsData)

        for quotes in self.flightsData['Quotes']:
            destination, destination_city, destination_country = self.getDestination(
                quotes['OutboundLeg']['DestinationId'])
            carriers = self.getCarrier(quotes['OutboundLeg']['CarrierIds'])
            origin, origin_city, origin_country = self.getOrigin(
                quotes['OutboundLeg']['OriginId'])
            minPrice = quotes['MinPrice']
            quoteDateTime = quotes['QuoteDateTime']
            direct = quotes['Direct']
            processedData.append({
                'destination': destination,
                'destination_city': destination_city,
                'destination_country': destination_country,
                'carriers': carriers,
                'origin': origin,
                'origin_city': origin_city,
                'origin_country': origin_country,
                'minPrice': minPrice,
                'quoteDateTime': quoteDateTime,
                'direct': direct
            })
        return processedData


class SendBookingConfirmation(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email_address = request.data['email_address']
        hotel_object = request.data['hotel_object']
        subject = 'Hotel Booking Confirmation'
        message = f'Dear {email_address},\n\nYour booking has been confirmed. Here are the details:\n\n{hotel_object}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email_address, ]
        send_mail(subject, message, email_from, recipient_list)
        return JsonResponse({'message': 'Email sent successfully'})




class BrowseRoutes(APIView):
    permission_classes = [AllowAny]

    # def post(self, request, *args, **kwargs):
    #     user_id = request.headers.get('user_id', None)
    #     if user_id:
    #         userExists = NewUser.objects.filter(id=user_id).all()
    #         if len(userExists) > 0:
    #             serializer = serializers.BrowseRouteModelFormSerializer(data=request.data)
    #             if serializer.is_valid():
    #                 flightsBrowseRoutesURL = '{0}browseroutes/v1.0/{1}/{2}/en-US/{3}/{4}/{5}/{6}'.format(
    #                     FLIGHTS_API_URL, request.data['country'], request.data['currency_format'],
    #                     request.data['origin'], request.data['destination'],
    #                     request.data['departureDate'], request.data['returnDate'])
    #                 result = requests.get(flightsBrowseRoutesURL, {'apiKey': FLIGHTS_API_KEY})
    #
    #                 if (result.status_code == 200):
    #                     getFlightsData = OfflineFlightsData(json.loads(result.text)).processFlights()
    #                     return Response(getFlightsData, status=status.HTTP_200_OK)
    #                 else:
    #                     return Response({'message': 'Something went wrong'},
    #                                     status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    #             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #         return Response({'message': 'No user exists with this id'}, status=status.HTTP_401_UNAUTHORIZED)
    #     return Response({'message': 'No user id found'}, status=status.HTTP_406_NOT_ACCEPTABLE)


def storeLocaleInformation(request):
    localeURL = '{0}reference/v1.0/locales'.format(FLIGHTS_API_URL)
    result = requests.get(localeURL, {'apiKey': FLIGHTS_API_KEY})

    if (result.status_code == 200):
        models.LocaleModel.objects.all().delete()
        try:
            models.LocaleModel.objects.bulk_create(
                [
                    models.LocaleModel(
                        code=i['Code'],
                        name=i['Name'],
                    )
                    for i in json.loads(result.text)['Locales']
                ]
            )
            return JsonResponse({"message": "bulk saving success"}, status=200)
        except Exception as e:
            return JsonResponse({"message": "bulk saving exception"}, status=400)
    else:
        return JsonResponse({'message': 'Something went wrong'}, status=500)


def storeCurrenciesInformation(request):
    currenciesURL = '{0}reference/v1.0/currencies'.format(FLIGHTS_API_URL)
    result = requests.get(currenciesURL, {'apiKey': FLIGHTS_API_KEY})

    if (result.status_code == 200):
        models.CurrencyModel.objects.all().delete()
        try:
            models.CurrencyModel.objects.bulk_create(
                [
                    models.CurrencyModel(
                        code=i['Code'],
                        symbol=i['Symbol'],
                        thousands_separator=i['ThousandsSeparator'],
                        decimal_separator=i['DecimalSeparator'],
                        symbol_on_left=i['SymbolOnLeft'],
                        space_between_amount_and_symbol=i['SpaceBetweenAmountAndSymbol'],
                        rounding_coefficient=i['RoundingCoefficient'],
                        decimal_digits=i['DecimalDigits']
                    )
                    for i in json.loads(result.text)['Currencies']
                ]
            )
            return JsonResponse({"message": "bulk saving success"}, status=200)
        except Exception as e:
            return JsonResponse({"message": "bulk saving exception"}, status=400)
    else:
        return JsonResponse({'message': 'Something went wrong'}, status=500)


class LiveFlightsData:

    def __init__(self, flightsData):
        self.flightsData = flightsData

    def processTravelDateold(self, travel_date):
        travel_date = datetime.datetime.strptime(travel_date, "%Y-%m-%dT%H:%M:%S")
        date_str = travel_date.date()
        travel_time = travel_date.time()
        time_str = travel_time.strftime("%I:%M %p")
        return {
            'date': date_str,
            'time': time_str
        }

    def processTravelDate(self, departure_time_dict):

        # Create a datetime object from the 'departureDateTime' dictionary
        dt = datetime.datetime(departure_time_dict['year'], departure_time_dict['month'], departure_time_dict['day'], departure_time_dict['hour'], departure_time_dict['minute'], departure_time_dict['second'])

        # Format the datetime object as a string in the desired format
        departure_time_string = dt.strftime("%Y-%m-%dT%H:%M:%S")

        # Split the date and time into separate variables
        date_str = dt.date()
        time_str = dt.time().strftime("%I:%M %p")

        return {
            'date': date_str,
            'time': time_str
        }


    def getLegDetails(self, id):
        # details.update(self.getLegDetails(flightDataItinerariesList[0][0])) #LEGS
        flightDataItinerariesList = list(self.flightsData['content']['results']['legs'].items())
        # print(flightDataItinerariesList)

        # with open('C:\games\sample.txt', 'w') as f:
        #     print(flightDataItinerariesList, file=f)
        # print(flightDataItinerariesList)


        # for value in flightDataItinerariesList:
            # print(value[0])
            # print(value[1]['destinationPlaceId'])

            # with open('C:\games\sample.txt', 'w') as f:
            #     print(value, file=f)

              # borigin_station = self.getPlaces(value['legIds']['originPlaceId'])
              # destination_station = self.getPlaces(value['destinationPlaceId'])
              # departure = self.processTravelDate(value['departureDateTime']['year'])
              # arrival = self.processTravelDate(value['arrivalDateTime']['year'])

        for value in flightDataItinerariesList:
           # print(value['legIds'][0])
         if value[0] == id:
            origin_station = self.getPlaces(value[1]['originPlaceId'])
            destination_station = self.getPlaces(value[1]['destinationPlaceId'])
            departure = self.processTravelDate(value[1]['departureDateTime'])
            arrival = self.processTravelDate((value[1]['arrivalDateTime']))
#                 TODO FIX SO IT HAS THE ENTIRE DATE
            total_duration = value[1]['durationInMinutes']
            days = int(total_duration / 1440)  # 1440 -> total minutes in a day
            left_minutes = total_duration % 1440
            hours = int(left_minutes / 60)
            minutes = total_duration - (days * 1440) - (hours * 60)
            number_of_stops = value[1]['stopCount']
            carriers = self.getCarrier(value[1]['operatingCarrierIds'][0])

            return {
                'origin_station': origin_station,
                'destination_station': destination_station,
                'departure': departure,
                'arrival': arrival,
                'total_duration': {
                    'days': days,
                    'hours': hours,
                    'minutes': minutes
                },
                'number_of_stops': number_of_stops,
                'carriers': carriers
            }

    def getAgentOLD(self, id):
        for agent in self.flightsData['Agents']:
            if agent['Id'] == id:
                return {
                    'name': agent['Name'],
                    'image': agent['ImageUrl']
                }

    def getAgent(self, id):
        for agent in list(self.flightsData['content']['results']['agents'].items()):
            if agent[0] == id:
                return {
                    'name': agent[1]['name'],
                    'image': agent[1]['imageUrl']
                }

    def getPlaces(self, id):
        # print(list(self.flightsData['content']['results']['places'].items()))
        for place in list(self.flightsData['content']['results']['places'].items()):
            if place[1]['entityId'] == id:
                return place[1]['name']

    def getCarrier(self, id):
        for carrier in list(self.flightsData['content']['results']['carriers'].items()):
            if carrier[0] == id:
                return carrier[1]['name']

    def processFlights(self):
        finalList = {}
        processedData = []
        print("processFlightsprocessFlightsprocessFlightsprocessFlightsprocessFlights")
        print(self.flightsData)

        # flightDataItinerariesList = list(self.flightsData.items())
        flightDataItinerariesList = list(self.flightsData['content']['results']['itineraries'].items())

        # print(type(flightDataItinerariesList[3][0][0][0]))
        # print(flightDataItinerariesList[3][0][0][0])


        # aList = list(flightDataItinerariesList[0])
        #
        # aList2 = list(aList[1])
        #
        # aList3 = list(aList2[0])
        #
        # print(aList3)
        # print(type(self.flightsData['content']['results']['itineraries']['13981-2212140600--31694-0-16692-2212140725']['pricingOptions'][0]['items'][0]['agentId']))
        # print(self.flightsData['content']['results']['itineraries']['13981-2212140600--31694-0-16692-2212140725']['pricingOptions'][0]['items'][0]['agentId'])

    # details.update(self.getLegDetails(flightDataItinerariesList[0][0])) #LEGS
    # print(self.flightsData['content']['results']['itineraries']['13981-2212140600--31694-0-16692-2212140725']['legIds'][0])
    
    
    # details['price'] = flight['PricingOptions'][0]['Price'] #PRICE
    # print(self.flightsData['content']['results']['itineraries']['13981-2212140600--31694-0-16692-2212140725']['pricingOptions'][0]['price']['amount'])
        
    # details['booking_deep_link'] = flight['PricingOptions'][0]['DeeplinkUrl'] #DEEPLINK
    # print(self.flightsData['content']['results']['itineraries']['13981-2212140600--31694-0-16692-2212140725']['pricingOptions'][0]['items'][0]['deepLink'])

    # details['agent'] = self.getAgent(flight['PricingOptions'][0]['Agents'][0]) #AGENT
    #   print(self.flightsData['content']['results']['itineraries']['13981-2212140600--31694-0-16692-2212140725']['pricingOptions'][0]['items'][0]['agentId'])

        # we need price and leg ids and to loop over each key and get both

        # res = next(iter(flightDataItinerariesList))

        # print(res)

        # we need to iterate through each key and update the methods to how we access them as above and hopefully after we are sweet

        # print("check below")
        #
        # for key, value in flightDataItinerariesList:
        #     print(value['pricingOptions'][0]['items'][0]['agentId'])
        # quit()
        # print(self.flightsData)

        # for key, value in flightDataItinerariesList:
        #     print(value['legIds'][0])


        for key, value in flightDataItinerariesList:
            details = {}
            details.update(self.getLegDetails(value['legIds'][0]))
            details['price'] = value['pricingOptions'][0]['price']['amount']
            details['booking_deep_link'] = value['pricingOptions'][0]['items'][0]['deepLink']
            details['agent'] = self.getAgent(value['pricingOptions'][0]['items'][0]['agentId'])
            processedData.append(details)
        processedData.sort(key=lambda x: x['price'], reverse=False)
        # print("number of flights==========", len(processedData))
        # print("processed final list==========", processedData)
        processedData[0]['cheapest'] = True

        finalList['list'] = processedData
        return finalList


        # for flight in self.flightsData['content']['results']['itineraries']:
        #     details = {}
        #     print("below is flight leg ids")
        #     print(flight[2])
        #     details.update(self.getLegDetails(flightDataItinerariesList[0][0]))
        #     details['price'] = flight['PricingOptions'][0]['Price']
        #     details['booking_deep_link'] = flight['PricingOptions'][0]['DeeplinkUrl']
        #     details['agent'] = self.getAgent(flight['PricingOptions'][0]['Agents'][0])
        #     processedData.append(details)
        # processedData.sort(key=lambda x: x['price'], reverse=False)
        # # print("number of flights==========", len(processedData))
        # # print("processed final list==========", processedData)
        # processedData[0]['cheapest'] = True
        #
        # finalList['currency'] = self.flightsData['Currencies'][0]['Symbol']
        # finalList['list'] = processedData
        # return finalList


class FlightLivePrices(APIView):
    permission_classes = [AllowAny]
    print("WE ARE IN THE FLIGHT LIVE PRICES")

    def getPollResults(self):
        print("below is session token in poll")
        print(self.sessionToken)
        pollResultsURL = FLIGHTS_API_URL + 'v3/flights/live/search/poll/' + self.sessionToken
        print(pollResultsURL)
        headers = {'x-api-key': FLIGHTS_API_KEY, 'Content-Type': 'application/json'}
        print(headers)
        result = requests.post(
            pollResultsURL, headers=headers,
        )
        print("below is result")
        print(json.loads(result.text))

        if (result.status_code == 200):
            print("we are in poll")
            print(LiveFlightsData(json.loads(result.text)).processFlights())
            getFlightsData = LiveFlightsData(json.loads(result.text)).processFlights()
            print("below is flightdatsa")
            print(getFlightsData)
            return getFlightsData
        else:
            print("WE GOT A ERROR HERE")
            return []

    def post(self, request, *args, **kwargs):
        print("WE ARE IN LIVE FLIGHTS POST REQUEST NOW")
        user_id = request.data['user_id']
        print("THIS IS REQUEST")
        print(request.data)
        if user_id:
            userExists = NewUser.objects.filter(id=user_id).all()
            ## user serializer.. will help to log the details for search history
            user = user_serializer.AddFlightSearchHistory(data=request.data)
            if user.is_valid():
                user.save()
            ## flights serializer
            print("WE ARE IN THE SERIALIZER")
            headers = {'x-api-key': FLIGHTS_API_KEY, 'Content-Type': 'application/json'}

            serializer = serializers.FlightsLiveModelFormSerializer(data=request.data)
            if serializer.is_valid():
                print("SERIALIZER is valid")
                date_obj_outbounddate = datetime.datetime.strptime(request.data['outbounddate'], '%Y-%m-%d')
                if "inbounddate" in request.data:
                    date_obj_inbounddate = datetime.datetime.strptime(request.data['inbounddate'], '%Y-%m-%d')
                else:
                    date_obj_inbounddate = None

                print("WE ARE IN THE INBOUND DATE")
                liveFlightsPricingURL = FLIGHTS_API_URL + 'v3/flights/live/search/create'

                query_legs = [
                    {
                        "originPlaceId": {
                            "iata": request.data['originplace'].removesuffix('-sky')
                        },
                        "destinationPlaceId": {
                            "iata": request.data['destinationplace'].removesuffix('-sky')
                        },
                        "date": {
                            "year": date_obj_outbounddate.year,
                            "month": date_obj_outbounddate.month,
                            "day": date_obj_outbounddate.day
                        }
                    }
                ]

                if date_obj_inbounddate is not None:
                    query_legs.append({
                        "originPlaceId": {
                            "iata": request.data['destinationplace'].removesuffix('-sky')
                        },
                        "destinationPlaceId": {
                            "iata": request.data['originplace'].removesuffix('-sky')
                        },
                        "date": {
                            "year": date_obj_inbounddate.year,
                            "month": date_obj_inbounddate.month,
                            "day": date_obj_inbounddate.day
                        }
                    })

                data = {
                    "query": {
                        'market': request.data['country'],
                        'currency': request.data['currency'],
                        'locale': request.data['locale'],
                        'adults': request.data['adults'],
                        "queryLegs": query_legs,
                        "childrenAges": [],
                        "cabinClass": "CABIN_CLASS_ECONOMY",
                        "excludedAgentsIds": [],
                        "excludedCarriersIds": [],
                        "includedAgentsIds": [],
                        "includedCarriersIds": []
                    }
                }

                print("THIS IS DATA")
                print(data)
                print("THIS IS URL")
                print(liveFlightsPricingURL)
                result = requests.post(
                    liveFlightsPricingURL,
                    data=json.dumps(data),
                    headers=headers,
                )
                print("below is json request")
                print(json.dumps(data))
                print("below is status code")
                print(result.status_code)

                if (result.status_code == 200):
                    print("SUCCESS")
                    response_data = result.json()
                    self.sessionToken = response_data['sessionToken']
                    print("below is session token in create")
                    print(self.sessionToken)
                    results = self.getPollResults()
                    original_stdout = sys.stdout

                    # with open('C:/filewrite/flights.txt', 'w') as f:
                    #     sys.stdout = f
                    #     print('Hello, Python!')
                    #     print(json.dumps(results, indent=4, sort_keys=True, default=str))
                    #     # Reset the standard output
                    #     sys.stdout = original_stdout

                    return Response({
                        'message': 'Found {} results'.format(len(results['list'] )),
                        'list': results['list'],
                        # 'message': 'Found {} results'.format(len(results['content']['results']['legs'])),
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({'message': 'Search query is invalid'},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'No user id found'}, status=status.HTTP_406_NOT_ACCEPTABLE)

class Cache:
    def __init__(self):
        self.cache = {}

    def set(self, key, value, timeout):
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + timeout
        }

    def get(self, key):
        if key not in self.cache:
            return None

        cached_value = self.cache[key]

        if time.time() > cached_value['expires_at']:
            del self.cache[key]
            return None

        return cached_value['value']

cache = Cache()
class CacheFlightHotelsPackage(APIView):
    permission_classes = [AllowAny]
    CACHE_KEY = 'best_packages_list'
    CACHE_TIMEOUT = 4 * 60 * 60  # 4 hours in seconds

    def hitFlightUrl(self, data, tripDays):
        country_name = hotelModels.HotelCountry.objects.filter(country_code=data['country']).first()
        finalFlightsList = []

        outbound_date = datetime.datetime.strptime(data['outbounddate'], '%Y-%m-%d')
        selected_year = outbound_date.year
        selected_month = outbound_date.month

        flights_indicative_search_url = f'{FLIGHTS_API_URL}v3/flights/indicative/search'
        print("Below is data recieved fromt front end")
        print(data)
        legs = [
            {
                "originPlace": {
                    "queryPlace": {
                        "iata": data['originplace'].removesuffix('-sky')
                    }
                },
                "destinationPlace": {
                    "queryPlace": {
                        "iata": data['destinationplace'].removesuffix('-sky')
                    }
                },
                "date_range": {
                    "startDate": {
                        "year": selected_year,
                        "month": selected_month
                    },
                    "endDate": {
                        "year": selected_year,
                        "month": selected_month
                    }
                }
            }
        ]
        
        if 'inbounddate' in data:
            legs.append({
                "originPlace": {
                    "queryPlace": {
                        "iata": data['destinationplace'].removesuffix('-sky')
                    }
                },
                "destinationPlace": {
                    "queryPlace": {
                        "iata": data['originplace'].removesuffix('-sky')
                    }
                },
                "date_range": {
                    "startDate": {
                        "year": selected_year,
                        "month": selected_month
                    },
                    "endDate": {
                        "year": selected_year,
                        "month": selected_month
                    }
                }
            })
        
        payload = {
            "query": {
                "currency": data['currency_format'],
                "locale": "en-US",
                "market": data['country'],
                "dateTimeGroupingType": "DATE_TIME_GROUPING_TYPE_BY_DATE",
                "queryLegs": legs
            }
        }

        print("this is payload")
        print(payload)

        headers = {'x-api-key': FLIGHTS_API_KEY, 'Content-Type': 'application/json'}

        print(headers)


        try:
            result = requests.post(flights_indicative_search_url, headers=headers, json=payload)
            result.raise_for_status()
            jsonResult = result.json()

            quotes = jsonResult.get('content', {}).get('results', {}).get('quotes', {})
            if quotes:
                for quote_key, quote_data in quotes.items():
                    outbound_date = datetime.date(quote_data['outboundLeg']['departureDateTime']['year'],
                                                  quote_data['outboundLeg']['departureDateTime']['month'],
                                                  quote_data['outboundLeg']['departureDateTime']['day'])

            has_inbound_date = 'inbounddate' in data

            if quotes:
                for quote_key, quote_data in quotes.items():
                    outbound_date = datetime.date(quote_data['outboundLeg']['departureDateTime']['year'],
                                                  quote_data['outboundLeg']['departureDateTime']['month'],
                                                  quote_data['outboundLeg']['departureDateTime']['day'])

                    if has_inbound_date and 'inboundLeg' in quote_data:
                        inbound_date = datetime.date(quote_data['inboundLeg']['departureDateTime']['year'],
                                                     quote_data['inboundLeg']['departureDateTime']['month'],
                                                     quote_data['inboundLeg']['departureDateTime']['day'])
                    else:
                        inbound_date = outbound_date + datetime.timedelta(days=tripDays)

                    days_between = inbound_date - outbound_date
                    if days_between.days == tripDays:
                        print(outbound_date, " TO ", inbound_date)
                        finalFlightsList.append({
                            'outbounddate': outbound_date.strftime('%Y-%m-%d'),
                            'inbounddate': inbound_date.strftime('%Y-%m-%d'),
                            'carrier_name': "",
                            'price': float(quote_data['minPrice']['amount']),
                            'country': model_to_dict(country_name)['country_name'],
                        })


        except requests.exceptions.HTTPError as e:
            finalFlightsList.append({
                'outbounddate': '01/08/2022',
                'inbounddate': '04/08/2022',
                'carrier_name': '',
                'price': 0
            })

        return finalFlightsList



    def getLiveFlightsWhenNoResultsForCache(self, request_data):
        print("belwowoowowow")
        trip_days = request_data['trip_days']
        print(request_data)
        country_name = hotelModels.HotelCountry.objects.filter(country_code=request_data['country']).first()
        finalFlightsList = []
        flights_indicative_search_url = FLIGHTS_API_URL + 'v3/flights/live/search/create'
        headers = {'x-api-key': FLIGHTS_API_KEY, 'Content-Type': 'application/json'}
        for i in range(3):
            outbound_date_obj = datetime.datetime.strptime(request_data['outbounddate'], '%Y-%m-%d')
            outbound_date_obj += timedelta(days=i)
            selected_year, currentMonth, outboundDay = outbound_date_obj.year, outbound_date_obj.month, outbound_date_obj.day

            inbound_date_obj = None
            inbound_date_str = request_data.get('inbounddate', None)
            if inbound_date_str:
                inbound_date_obj = datetime.datetime.strptime(inbound_date_str, '%Y-%m-%d')
                inbound_date_obj += timedelta(days=i)
            else:
                print("The 'inbounddate' key is not present in the request_data dictionary.")

            if inbound_date_obj:
                _, _, returnDay = inbound_date_obj.year, inbound_date_obj.month, inbound_date_obj.day
            else:
                returnDay = None

            query_legs = [
                {
                    "originPlaceId": {
                        "iata": request_data['originplace'].removesuffix('-sky')
                    },
                    "destinationPlaceId": {
                        "iata": request_data['destinationplace'].removesuffix('-sky')
                    },
                    "date": {
                        "year": selected_year,
                        "month": currentMonth,
                        "day": outboundDay
                    }
                }
            ]

            if inbound_date_obj is not None:
                query_legs.append({
                    "originPlaceId": {
                        "iata": request_data['originplace'].removesuffix('-sky')
                    },
                    "destinationPlaceId": {
                        "iata": request_data['destinationplace'].removesuffix('-sky')
                    },
                    "date": {
                        "year": selected_year,
                        "month": currentMonth,
                        "day": returnDay
                    }
                })

            data = {
                "query": {
                    'market': request_data['country'],
                    'currency': request_data['currency_format'],
                    'locale': "en-US",
                    'adults': request_data['adults'],
                    "queryLegs": query_legs,
                    "childrenAges": [],
                    "cabinClass": "CABIN_CLASS_ECONOMY",
                    "excludedAgentsIds": [],
                    "excludedCarriersIds": [],
                    "includedAgentsIds": [],
                    "includedCarriersIds": []
                }
            }

            print("this is request being sent")
            print(data)

            try:
                result = requests.post(flights_indicative_search_url, headers=headers, data=json.dumps(data))
                result.raise_for_status()
                jsonResult = result.json()
                file_path = "C:/FlightDuck/flight-duck-backend-aws-main/flights/flights_output_skyscanner.txt"
                flights_json = json.dumps(jsonResult)
                with open(file_path, 'w') as file:
                    file.write(flights_json)

                if jsonResult.get('content', {}).get('results', {}).get('itineraries', None):
                    itineraries = jsonResult['content']['results']['itineraries']
                    for itinerary_id, itinerary in itineraries.items():
                        if itinerary.get('pricingOptions', None):
                            for option in itinerary['pricingOptions']:
                                price = option['price']['amount']
                                carrier_name = None
                                if option.get('items', None):
                                    item = option['items'][0]
                                    if item.get('fares', None):
                                        carrier_name = option['agentIds'][0]

                                finalFlightsList.append({
                                    'outbounddate': datetime.datetime.strptime(request_data['outbounddate'], '%Y-%m-%d').strftime('%Y-%m-%d'),
                                    'inbounddate': (datetime.datetime.strptime(request_data['outbounddate'], '%Y-%m-%d') + timedelta(days=trip_days)).strftime('%Y-%m-%d'),
                                    'carrier_name': carrier_name,
                                    'price': price,
                                    'country': model_to_dict(country_name)['country_name']
                                })


                        else:
                            finalFlightsList.append({
                                'outbounddate': outboundDay,
                                'inbounddate': returnDay,
                                'carrier_name': '',
                                'price': 0
                            })
            except requests.exceptions.HTTPError as e:
                print("flight requests exception========", e)
                print("for date====", outboundDay)
                print()
                finalFlightsList.append({
                    'outbounddate': outboundDay,
                    'inbounddate': returnDay,
                    'carrier_name': '',
                    'price': 0
                })
        # print("bebloiw is finalflights")
        # print(finalFlightsList)
        # file_path = "C:/FlightDuck/flight-duck-backend-aws-main/flights/flights_output.txt"
        # flights_json = json.dumps(finalFlightsList)
        # with open(file_path, 'w') as file:
        #     file.write(flights_json)
        return finalFlightsList



    def getOfflineFlightsResult(self, data):
        tripDays = int(data['trip_days'])
        finalFlightsList = []
        # make below into a function then we will call it with the days variable and if returned 0 then we add 1 to the days and try again. If that doesnt work then - 1 and then if that doesnt work then thats it.
        # Also if the return date is in the same month and its more days then whats left in the month then we go to the next month. Watch out for double digits!
        finalFlightsList = self.hitFlightUrl(data, tripDays)
        # if len(finalFlightsList) < 3:
        #     print("god i hope this works")
        #     finalFlightsList = self.getLiveFlightsWhenNoResultsForCache(data)
        # finalFlightsList = self.getLiveFlightsWhenNoResultsForCache(data)
        return finalFlightsList

    def list_split(self, listA, n):
        print("below is listA")
        print(listA)
        print("below is n")
        print(n)
        for x in range(0, len(listA), n):
            every_chunk = listA[x: n + x]

            if len(every_chunk) < n:
                every_chunk = every_chunk + \
                              []
            yield every_chunk

    def getHotelDeals(self, requestData, flightList):
        liveHotelsPricingURL = HOTELS_API_URL + '/hotel-api/1.0/hotels'
        headers_dict = {
            "Api-key": HOTELS_API_KEY,
            "X-Signature": createXSignature(),
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json"
        }
        # hotelsList = list(hotelModels.HotelDetail.objects.filter(destination_code=requestData['destination_code']).values_list('code', flat=True))
        # print("hotelsList========", hotelsList)
        print("below is requestdata")
        print(requestData)
        date = datetime.datetime.strptime(requestData['outbounddate'], '%Y-%m-%d')
        numberOfMonthsToTry = date.month + requestData['number_of_extended_months']
        numberOfDaysInMonth = monthrange(date.year, date.month)
        tripDays = int(requestData['trip_days'])
        finalHotelsList = []
        graphList = []
        print("below is type")
        # flightObj = flightList[0]['outbounddate']
        # print(flightObj)
        # print(type(flightObj))
        # print(list(hotelModels.HotelDetail.objects.filter(destination_code=requestData['destination_code']).values_list('code', flat=True))[0])
        # print(list(hotelModels.HotelDetail.objects.filter(destination_code=requestData['destination_code']).values_list('code', flat=True)))
        hotelCodes = list(
            hotelModels.HotelDetail.objects.filter(
                destination_code=requestData['destination_code'],
                city__iexact=requestData['destinationName']
            ).values_list('code', flat=True)
        )


        # hotelListDivided = np.array_split(hotelCodes, len(flightList))
        print("below is destination code")
        print(requestData['destination_code'])
        print("below is hotelCodes")
        print(len(hotelCodes))
        print("below is flight")
        print(len(flightList))
        divideBy = int(int(len(hotelCodes)) / (int(len(flightList))))
        print("hotelcodes and flight below")
        print(int(int(len(hotelCodes))))
        print((int(len(flightList))))
        hotelListDivided = list(self.list_split(hotelCodes, divideBy))

        # print("this is divided 0")
        # print(hotelListDivided[0])
        # print("this is divided length")
        # print(len(hotelListDivided))
        # print("this is flights len")
        # print(len(flightList))
        # print("EQUATUION")
        # print(yep)
        # print("this is hotel codes length")
        # print(hotelCodesLength)
        # print("this is flights length")
        # print(len(flightList))
        # yousee = json_dump = json.dumps(hotelListDivided,
        #                cls=NumpyEncoder)
        # print(json_dump)
        # yousee = pd.Series(hotelListDivided).to_json(orient='values')

        currentHotelListSection = 0

        print("This is flight list that is being passed to the loop")
        print(len(flightList))
        print("This is hotel list that needs to be equal or less then flights")
        print(len(hotelListDivided))

        print("THIS IS HOTELREQUESTDATATATA")
        print(requestData)

        for i in flightList:
            # algo to divide array into 5's (but play around) and then loop through that array on the condition that if the next set of numbers is greater then grab the last numbers and
            # restart the loop
            # Above this loop we divide the hotel codes list based on the amount of flightlist dates so we get all numbers. Then hit them
            print("this is current hotel list section")
            print(currentHotelListSection)
            outBoundDate = i['outbounddate']
            inBoundDate = i['inbounddate']

            data = {
                "stay": {
                    "checkIn": outBoundDate,
                    "checkOut": inBoundDate,
                },
                "occupancies": [
                    {
                        "rooms": requestData['rooms'],
                        "adults": requestData['adults'],
                        "children": requestData['children']
                    }
                ],
                # "destination": {
                #     "code": requestData['destination_code']
                # }
                "hotels": {
                    "hotel": hotelListDivided[currentHotelListSection]
                }
            }
            # print(liveHotelsPricingURL)
            print("this is what we are hitting hotel")
            print(data)
            try:
                result = requests.post(
                    liveHotelsPricingURL,
                    json=data,
                    headers=headers_dict
                )
                print(data)
                if (currentHotelListSection == len(hotelListDivided) - 1):
                    currentHotelListSection = 0
                else:
                    currentHotelListSection += 1

                # print("result======", result.status_code)
                result.raise_for_status()
                jsonData = json.loads(result.text)
                hotel_object = {}
                if (jsonData.get('hotels', None)):
                    hotelBedsList = jsonData['hotels'].get('hotels', None)
                    # print("this is hotel beds list")
                    # print(hotelBedsList)

                    # print("SIZE OF ARRAY BELOW")
                    # print(len(hotelBedsList))
                    # print("cheapest hotel==========", hotelBedsList)
                    # if hotelBedsList:
                    #     hotel_name = hotelBedsList[0]['name']
                    #     hotel_city = hotelBedsList[0]['destinationName']
                    #     cheapestPrice = hotelBedsList[0]['minRate']
                    #     cheapestHotelCode = hotelBedsList[0]['code']
                    #     complete_object = hotelBedsList
                    # TODO: What we actually want to do is take the first 5 hotels from the list and then grab the next 5 from the next api call and so on
                    if (hotelBedsList is not None):
                        for i in hotelBedsList:
                            # if ((i['minRate']<cheapestPrice) & (hotelModels.HotelDetail.objects.filter(code=i['code']).first() is not None)):
                            hotel_name = i['name']
                            hotel_city = i['destinationName']
                            cheapestPrice = i['minRate']
                            cheapestHotelCode = i['code']
                            complete_object = i

                            hotel = hotelModels.HotelDetail.objects.filter(code=cheapestHotelCode).first()

                            if hotel is None:
                                print("hotel is none")
                            if hotel is not None:
                                # print("complete object=====", complete_object)
                                hotel_object['hotel'] = model_to_dict(hotel)['name']
                                images = hotelModels.HotelImage.objects.filter(hotel_id=hotel.id).all()
                                if len(images) > 0:
                                    hotel_images = [HOTELS_PHOTOS_BASE_URL + image['image_url'] for image in
                                                    images.values('image_url')]
                                    hotel_object['images'] = hotel_images
                                    hotel_details = {}
                                    if type(complete_object) is list:
                                        hotel_details.update(getHotelDetailsBasedOnCode(complete_object[i]))
                                        hotel_details['rate'] = float(complete_object[i]['minRate'])
                                        hotel_details['rooms'] = complete_object[i]['rooms']
                                    else:
                                        hotel_details.update(getHotelDetailsBasedOnCode(complete_object))
                                        hotel_details['rate'] = float(complete_object['minRate'])
                                        hotel_details['rooms'] = complete_object['rooms']
                                    # print("complete object=========\n", complete_object, "\n\n")
                                    # print("complete object===== \n", getHotelDetailsBasedOnCode(complete_object), "\n\n")
                                    # hotel_details.update(getHotelDetailsBasedOnCode(complete_object))
                                    # hotel_details['rate'] = float(complete_object['minRate'])
                                    # hotel_details['rooms'] = complete_object['rooms']
                                    print(outBoundDate)
                                    finalHotelsList.append({
                                        'outbounddate': outBoundDate,
                                        'inbounddate': inBoundDate,
                                        'price': cheapestPrice,
                                        'tripDays': tripDays,
                                        'hotel': hotel_object,
                                        # 'hotel_object': complete_object,
                                        # 'hotel_object': getHotelDetailsBasedOnCode(complete_object)
                                        'hotel_object': hotel_details
                                    })

            except requests.exceptions.HTTPError as e:
                print("hotel requests exception========", e)
                print("for date====", outBoundDate)
                print()
                finalHotelsList.append({
                    'outbounddate': outBoundDate,
                    'inbounddate': inBoundDate,
                    'price': 0
                })
            except Exception as e:
                print("hotel exception=========", e)
                # print("for date====", outBoundDate)
                print("traceback========", traceback.format_exc())
                print()
                print()

            # if currentMonthWasIncreased == True:
            #     currentMonth = int(currentMonth)-1
        print("Below is finalhotels list length")
        print(len(finalHotelsList))
        return finalHotelsList

    def findCheapestPackages(self, bestPackagesList):
        date_price_dict = {}

        # Traverse through each package
        for package in bestPackagesList:
            date = package['outbounddate']
            price = package['deal_price']

            # If this date is not in the dictionary, or this price is cheaper than the current value, update the dictionary
            if date not in date_price_dict or price < date_price_dict[date]:
                date_price_dict[date] = price

        min_price = min(date_price_dict.values())

        # Create list of dictionaries with date, price, and color
        cheapest_prices_per_date = []
        for date, price in date_price_dict.items():
            if price == min_price:
                color = "green"
            elif price <= 1.4 * min_price:
                color = "orange"
            else:
                color = "red"
            cheapest_prices_per_date.append({"date": date, "price": price, "color": color})

        return cheapest_prices_per_date

    def findBestDealPackage(self, bestPackagesList):
        # Check if the list is not empty
        if bestPackagesList:
            # Find the cheapest package
            cheapest_package = next((package for package in bestPackagesList if package['cheapest'] == True), None)

            if cheapest_package:
                # Set the maximum price for the best deal as 40% more than the cheapest
                max_price = cheapest_package['deal_price'] * 1.40

                # Get packages that are under the max price and have ratings
                valid_packages = [package for package in bestPackagesList
                                  if 'deal_price' in package and package['deal_price'] <= max_price
                                  and 'hotel_object' in package
                                  and 'rating' in package['hotel_object']]

                if valid_packages:
                    # Get the package with the highest rating among the valid packages
                    best_deal_package = max(valid_packages, key=lambda x: x['hotel_object']['rating'])
                    # Mark the package as the 'bestDeal'
                    best_deal_package['bestDeal'] = True

        return bestPackagesList


    def findBestPackages(self, offlineFlightResults, hotelDeals):
        bestPackagesList = []
        number = 0
        for flight in offlineFlightResults:
            for hotel in hotelDeals:
                if (
                        (flight['outbounddate'] == hotel['outbounddate']) &
                        (float(hotel['price']) != 0) &
                        (float(flight['price']) != 0)
                ):
                    number += 1
                    total_price = float(flight['price']) + (float(hotel['price']))
                    bestPackagesList.append({
                        'outbounddate': flight['outbounddate'],
                        'inbounddate': flight['inbounddate'],
                        'flight_price': flight['price'],
                        'carrier_name': flight['carrier_name'],
                        'hotel_price': float(hotel['price']),
                        'tripDays': hotel['tripDays'],
                        'deal_price': round(total_price, 2),
                        'hotel': hotel['hotel']['hotel'] if hotel['hotel']['hotel'] else [],
                        'images': hotel['hotel']['images'] if hotel['hotel']['images'] else [],
                        'country': flight['country'],
                        'hotel_object': hotel['hotel_object'],
                        'cheapest': False,  # add a 'cheapest' attribute
                        'bestDeal': False  # Add a 'bestDeal' attribute
                    })
        cheapest_prices = self.findCheapestPackages(bestPackagesList)

        # Find the package with the lowest 'deal_price' and mark it as 'cheapest'
        if bestPackagesList:
            cheapest_package = min(bestPackagesList, key=lambda x: x['deal_price'])
            cheapest_package['cheapest'] = True

        bestPackagesList.append({'calendar': cheapest_prices})

        bestPackagesList = self.findBestDealPackage(bestPackagesList)

        return bestPackagesList


    def post(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        if user_id:
            userExists = NewUser.objects.filter(id=user_id).all()
            ## user serializer.. will help to log the details for search history
            user = user_serializer.AddFlightsHotelPackageHistory(data=request.data)
            if user.is_valid():
                user.save()

            ## flights hotel package serializer
            package_serializer = serializers.FlightsHotelPackageSerializer(data=request.data)
            if package_serializer.is_valid():
                # TODO: Use services.package_service

                # Generate a unique cache key based on request payload
                payload_hash = hashlib.sha256(repr(request.data).encode('utf-8')).hexdigest()
                unique_cache_key = f"{self.CACHE_KEY}_{payload_hash}"

                # Check cache
                cached_best_packages_list = cache.get(unique_cache_key)
                if cached_best_packages_list is not None:
                    # Use cached result
                    finalList = cached_best_packages_list
                else:
                    # Calculate result and cache it
                    offlineFlightData = self.getOfflineFlightsResult(data=request.data)
                    hotelDeals = self.getHotelDeals(requestData=request.data, flightList=offlineFlightData)
                    finalList = self.findBestPackages(offlineFlightData, hotelDeals)
                    cache.set(unique_cache_key, finalList, self.CACHE_TIMEOUT)

                return Response({
                    'message': 'Success',
                    'list': finalList
                }, status=status.HTTP_200_OK)

            return Response(package_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'No user id found'}, status=status.HTTP_406_NOT_ACCEPTABLE)




class GetCountries(APIView):
    permission_classes = [AllowAny]

    def getAirportCode(self, countryName, airportName):
        autoSuggestURL = FLIGHTS_API_URL + \
                         'autosuggest/v1.0/US/GBP/en-US/?query={}&apiKey={}' \
                             .format(airportName, FLIGHTS_API_KEY)

        result = requests.get(
            autoSuggestURL
        )

        if (result.status_code == 200):
            jsonData = json.loads(result.text)
            places = jsonData['Places']
            placeId = 'NA'
            if len(places) > 0:
                for place in places:
                    print("place=====", place)
                    # print()
                    if ((place['PlaceName'] == "Santa Cruz Is")):
                        break

                    if ((place['PlaceName'].lower() == airportName.lower()) &
                            (place['CountryName'].lower() == countryName.lower())):
                        print("place id =======", place['PlaceId'])
                        placeId = place['PlaceId']
                        break

                if placeId == 'NA':
                    print("not found=======")
                    print("country name======", countryName)
                    print("airport name======", airportName)
                    print()
                return placeId
            return ''

    def get(self, request, *args, **kwargs):
        models.CountryModel.objects.all().delete()
        models.CityModel.objects.all().delete()
        models.AirportModel.objects.all().delete()
        geoDataURL = FLIGHTS_API_URL + 'geo/v1.0?apikey=' + FLIGHTS_API_KEY

        result = requests.get(
            geoDataURL
        )

        if (result.status_code == 200):
            jsonData = json.loads(result.text)
            # print("jsonData======", jsonData)
            numberOfContinents = jsonData['Continents']
            print("NUMBER OF CONTINENTS ======", numberOfContinents)
            #             numberOfContinents = jsonData['Continents'][:1]
            # numberOfContinents = jsonData['Continents']
            continents_data = {}
            for continent in numberOfContinents:
                countries_list = []
                #                 for country in continent['Countries'][:10]:
                for country in continent['Countries']:
                    # if country['Id'] in ['MN', 'IN']:
                    country_object = models.CountryModel.objects.create(
                        country_code=country['Id'],
                        name=country['Name']
                    )
                    cities_list = []
                    # print("country details=======", country)
                    # for city in country['Cities'][:10]:
                    for city in country['Cities']:
                        airports_list = []
                        city_object = ''
                        try:
                            city_object = models.CityModel.objects.create(
                                city_name=city['Name'],
                                city_code=city['IataCode']
                            )
                        except:
                            pass
                            # print("exception for city_object======", city['Name'])
                            # city_object = models.CityModel.objects.filter(
                            #     city_code=city['IataCode']
                            # ).first()
                        for airport in city['Airports']:
                            code = self.getAirportCode(
                                country['Name'], airport['Name'])
                            if ((code != '') & (code != 'NA')):
                                airports_list.append({
                                    'name': airport['Name'],
                                    'code': code
                                })
                                try:
                                    models.AirportModel.objects.create(
                                        country=country_object,
                                        city=city_object,
                                        airport_name=airport['Name'],
                                        airport_code=code
                                    )
                                except Exception as e:
                                    pass
                        if len(airports_list) > 0:
                            cities_list.append({
                                'name': city['Name'],
                                'airports': airports_list
                            })
                    countries_list.append({
                        'code': country['Id'],
                        'country': country['Name'],
                        'cities': cities_list
                    })

                    continents_data[continent['Name']] = countries_list

            return Response({
                'continents': len(numberOfContinents),
                'countries_data': continents_data,
                'message': True
            }, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Search query is invalid'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # def get(self, request, *args, **kwargs):
    #     query = request.query_params.get('query')
    #     autoSuggestURL = FLIGHTS_API_URL + \
    #         'autosuggest/v1.0/US/GBP/en-US/?query={}&apiKey={}'\
    #         .format(query, FLIGHTS_API_KEY)

    #     result = requests.get(
    #         autoSuggestURL
    #     )

    #     if (result.status_code == 200):
    #         jsonData = json.loads(result.text)
    #         places = jsonData['Places']
    #         for place in places:
    #             print("place=====", place)
    #             print()
    #             if place['PlaceName'].lower() == query.lower():
    #                 print("place id =======", place['PlaceId'])

    #         return Response({
    #             'place': query,
    #             'message': True 
    #         }, status=status.HTTP_200_OK)
    #         # return Response({'jsonData': jsonData}, status=status.HTTP_200_OK)
    #     else:
    #         return Response({'message': 'Search query is invalid'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    #     # return Response({'message': 'Success'}, status=status.HTTP_200_OK)


# class GetAirportCode(APIView):
#     permission_classes = [AllowAny]

#     def get(self, request, *args, **kwargs):
#         query = request.query_params.get('query')
#         print("query=========", query)
#         if query is not None:
#             airports = list(models.AirportModel.objects.filter(
#                 airport_name__icontains=query
#             ).values(
#                 'airport_name', 'airport_code',
#                 'city__city_name', 'city__city_code')[:6])
#         else:
#             country = request.query_params.get('country')
#             airports = list(models.AirportModel.objects.filter(
#                 country__country_code__icontains=country
#             ).values('airport_name', 'airport_code',
#                      'city__city_name', 'city__city_code')[:6])
#         if (len(airports) > 0):
#             return Response({
#                 'list': airports
#             }, status=status.HTTP_200_OK)
#         else:
#             return Response({'list': []}, status=status.HTTP_406_NOT_ACCEPTABLE)

class GetAirportCode(APIView):
    permission_classes = [AllowAny]

def post(self, request, format='json'):
    # TODO change this endpoint for local based on country
    print("in autosuiggest")
    flights_destination_auto_suggestion = '{0}autosuggest/v3/geo/hierarchy/flights/en-AU'.format(FLIGHTS_API_URL)

    serializer = serializers.AutoSuggestModelFormSerializer(data=request.data)
    if serializer.is_valid():
        query = serializer.data['query']
        headers = {'apiKey': FLIGHTS_API_KEY}
        result = requests.get(flights_destination_auto_suggestion, params={'query': query}, headers=headers)

        if result.status_code == 200:
            response_data = json.loads(result.text)
            places_map = response_data['placesMap']
            # Filter out airports that do not serve commercial flights
            filtered_places = {k: v for k, v in places_map.items() if not (v['type'] == 'airport' and v['commercial'] == False)}
            # Flatten the response data
            flat_response = []
            for _, place in filtered_places.items():
                flat_response.append(place)
            return Response(flat_response, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)