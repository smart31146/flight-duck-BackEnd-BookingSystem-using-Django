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
from .services import package_service
from backend import settings
import numpy as np
import pandas as pd
import codecs

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
        flightsDestinationAutoSuggestion = '{0}autosuggest/v1.0/US/USD/en-US'.format(FLIGHTS_API_URL)
        
        serializer = serializers.AutoSuggestModelFormSerializer(data = request.data)
        if serializer.is_valid():
            query = serializer.data['query']
            result = requests.get(flightsDestinationAutoSuggestion, {'query': query, 'apiKey': FLIGHTS_API_KEY})

            if (result.status_code == 200):
                return Response(json.loads(result.text), status=status.HTTP_200_OK)
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


class BrowseRoutes(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        user_id = request.headers.get('user_id', None)
        if user_id:
            userExists = NewUser.objects.filter(id=user_id).all()
            if len(userExists)>0:
                serializer = serializers.BrowseRouteModelFormSerializer(data = request.data)
                if serializer.is_valid():
                    flightsBrowseRoutesURL = '{0}browseroutes/v1.0/{1}/{2}/en-US/{3}/{4}/{5}/{6}'.format(
                        FLIGHTS_API_URL, request.data['country'], request.data['currency_format'],
                        request.data['origin'], request.data['destination'], 
                        request.data['departureDate'], request.data['returnDate'])
                    result = requests.get(flightsBrowseRoutesURL, {'apiKey': FLIGHTS_API_KEY})

                    if (result.status_code == 200):
                        getFlightsData = OfflineFlightsData(json.loads(result.text)).processFlights()
                        return Response(getFlightsData, status=status.HTTP_200_OK)
                    else:
                        return Response({'message': 'Something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({'message': 'No user exists with this id'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'message': 'No user id found'}, status=status.HTTP_406_NOT_ACCEPTABLE)


def storeLocaleInformation(request):
    localeURL = '{0}reference/v1.0/locales'.format(FLIGHTS_API_URL)
    result = requests.get(localeURL, {'apiKey': FLIGHTS_API_KEY})

    if (result.status_code == 200):
        models.LocaleModel.objects.all().delete()
        try:
            models.LocaleModel.objects.bulk_create(
                [
                    models.LocaleModel(
                        code = i['Code'],
                        name = i['Name'],
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
                        code = i['Code'],
                        symbol = i['Symbol'],
                        thousands_separator = i['ThousandsSeparator'],
                        decimal_separator = i['DecimalSeparator'],
                        symbol_on_left = i['SymbolOnLeft'],
                        space_between_amount_and_symbol = i['SpaceBetweenAmountAndSymbol'],
                        rounding_coefficient = i['RoundingCoefficient'],
                        decimal_digits = i['DecimalDigits']
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

    def processTravelDate(self, travel_date):
        travel_date = datetime.datetime.strptime(travel_date, "%Y-%m-%dT%H:%M:%S")
        date_str = travel_date.date()
        travel_time = travel_date.time()
        time_str = travel_time.strftime("%I:%M %p")
        return {
            'date': date_str,
            'time': time_str
        }
    
    def getLegDetails(self, id):
        for leg in self.flightsData['Legs']: 
            if leg['Id'] == id:
                origin_station = self.getPlaces(leg['OriginStation'])
                destination_station = self.getPlaces(leg['DestinationStation'])
                departure = self.processTravelDate(leg['Departure'])
                arrival = self.processTravelDate(leg['Arrival'])
                total_duration = leg['Duration']
                days = int(total_duration / 1440) # 1440 -> total minutes in a day
                left_minutes = total_duration % 1440 
                hours = int(left_minutes / 60)
                minutes = total_duration - (days*1440) - (hours*60)
                number_of_stops = len(leg['Stops'])
                carriers = self.getCarrier(leg['Carriers'][0])

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

    def getAgent(self, id):
        for agent in self.flightsData['Agents']: 
            if agent['Id'] == id:
                return {
                    'name': agent['Name'],
                    'image': agent['ImageUrl']
                }

    def getPlaces(self, id):
        for place in self.flightsData['Places']: 
            if place['Id'] == id:
                return place['Name']

    def getCarrier(self, id):
        for carrier in self.flightsData['Carriers']: 
            if carrier['Id'] == id:
                return carrier['Name']

    def processFlights(self):
        finalList = {}
        processedData = []

        for flight in self.flightsData['Itineraries']:
            details = {}
            details.update(self.getLegDetails(flight['OutboundLegId']))
            details['price'] = flight['PricingOptions'][0]['Price']
            details['booking_deep_link'] = flight['PricingOptions'][0]['DeeplinkUrl']
            details['agent'] = self.getAgent(flight['PricingOptions'][0]['Agents'][0])
            processedData.append(details)
        processedData.sort(key=lambda x: x['price'], reverse=False)
        # print("number of flights==========", len(processedData))
        # print("processed final list==========", processedData)
        processedData[0]['cheapest'] = True

        finalList['currency'] = self.flightsData['Currencies'][0]['Symbol']
        finalList['list'] = processedData
        return finalList

class FlightLivePrices(APIView):
    permission_classes = [AllowAny]

    def getPollResults(self):
        pollResultsURL = FLIGHTS_API_URL + 'pricing/v1.0/' + self.sessionToken + "?apikey=" + FLIGHTS_API_KEY
        result = requests.get(
            pollResultsURL
        )
        
        if (result.status_code == 200):
            getFlightsData = LiveFlightsData(json.loads(result.text)).processFlights()
            return getFlightsData
        else:
            return []

    def post(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        print("THIS IS REQUEST")
        print(request.data)
        if user_id:
            userExists = NewUser.objects.filter(id=user_id).all()
            ## user serializer.. will help to log the details for search history
            user = user_serializer.AddFlightSearchHistory(data = request.data)
            if user.is_valid():
                user.save()
            ## flights serializer
            print("WE ARE IN THE SERIALIZER")
            serializer = serializers.FlightsLiveModelFormSerializer(data = request.data)
            if serializer.is_valid():
                print("SERIALIZER is valid")
                print(request.data)
                liveFlightsPricingURL = FLIGHTS_API_URL + 'pricing/v1.0'
                data = {
                    'country': request.data['country'], 
                    'currency': request.data['currency'], 
                    'locale': request.data['locale'], 
                    'locationSchema': 'iata',
                    'originplace': request.data['originplace'],
                    'destinationplace': request.data['destinationplace'],
                    'outbounddate': request.data['outbounddate'],
                    'inbounddate': request.data['inbounddate'],
                    'adults': request.data['adults'],
                    'apikey': FLIGHTS_API_KEY
                }
                print("THIS IS DATA")
                print(data)
                print("THIS IS URL")
                print(liveFlightsPricingURL)
                result = requests.post(
                    liveFlightsPricingURL,
                    data=data
                )
                print("below is status code")
                print(result.status_code)

                if (result.status_code == 201):
                    print("SUCCESS")
                    self.sessionToken = result.headers.get('Location').split('/')[-1]
                    results = self.getPollResults()
                    print(results)
                    return Response({
                        'message': 'Found {} results'.format(len(results['list'])), 
                        'list': results['list'],
                        'currency': results['currency']
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({'message': 'Search query is invalid'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'No user id found'}, status=status.HTTP_406_NOT_ACCEPTABLE)


class CacheFlightHotelsPackage(APIView):
    permission_classes = [AllowAny]

    def getOfflineFlightsResult(self, data):
        # this is hitting each date so making multiple api requests that can be done in one if we search for the whole month instead of individual dates
        print("this is data")
        print("HEYEHYEHHEHEYEHEYEHEHYERHEFYHEHFYEHFYEF")
        print(data)
        date = datetime.datetime.strptime(data['outbounddate'], '%Y-%m-%d')
        numberOfMonthsToTry = date.month + data['number_of_extended_months']
        numberOfDaysInMonth = monthrange(date.year, date.month)
        tripDays = int(data['trip_days'])
        date2 = '{:%Y-%m}'.format(datetime.datetime.strptime(data['outbounddate'], '%Y-%m-%d'))
        country_name = hotelModels.HotelCountry.objects.filter(country_code=data['country']).first()
        finalFlightsList = []
        flightsBrowseRoutesURL = '{0}browseroutes/v1.0/{1}/{2}/en-US/{3}/{4}/{5}/{6}'.format(
        FLIGHTS_API_URL, data['country'], data['currency_format'],
        data['originplace'], data['destinationplace'],
        date2, date2)
        try:
            result = requests.get(flightsBrowseRoutesURL, {'apiKey': FLIGHTS_API_KEY})
            result.raise_for_status()
            jsonResult = json.loads(result.text)

            # for loop that goes through each quote and adds to the array below and makes sure

            if jsonResult.get('Quotes', None):
                for quotes in jsonResult['Quotes']:
                    outboundDate = datetime.datetime.strptime(quotes['OutboundLeg']['DepartureDate'].split("T")[0], '%Y-%m-%d').date()
                    inboundDate = datetime.datetime.strptime(quotes['InboundLeg']['DepartureDate'].split("T")[0], '%Y-%m-%d').date()

                    daysBetween = inboundDate - outboundDate
                    # print(quotes['MinPrice'])
                    if len(jsonResult['Quotes']) > 0:
                        if daysBetween.days == tripDays:
                            print(outboundDate, " TO ", inboundDate)
                            finalFlightsList.append({
                                'outbounddate': quotes['OutboundLeg']['DepartureDate'].split("T")[0],
                                'inbounddate': quotes['InboundLeg']['DepartureDate'].split("T")[0],
                                'carrier_name': jsonResult['Carriers'][0]['Name'],
                                'price': quotes['MinPrice'],
                                'country': model_to_dict(country_name)['country_name'],
                            })
        except requests.exceptions.HTTPError as e:
            # print("flight requests exception========", e)
            # print("for date====", departureDate)
            # print()
            finalFlightsList.append({
                'outbounddate': '01/08/2022',
                'inbounddate': '04/08/2022',
                'carrier_name': '',
                'price': 0
            })
        # if currentMonthWasIncreased == True:
        #     currentMonth = int(currentMonth)-1
        #     print("THIS IS FLIGHTS", finalFlightsList)
        print("BELOW IS finalFlightsList")
        # print(finalFlightsList[3])
        print(len(finalFlightsList))
        return finalFlightsList

    def list_split(self, listA, n):
        for x in range(0, len(listA), n):
            every_chunk = listA[x: n+x]

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
            "Accept-Encoding":"gzip",
            "Content-Type": "application/json"
        }
        # hotelsList = list(hotelModels.HotelDetail.objects.filter(destination_code=requestData['destination_code']).values_list('code', flat=True))
        # print("hotelsList========", hotelsList)
        date = datetime.datetime.strptime(requestData['outbounddate'], '%Y-%m-%d')
        numberOfMonthsToTry = date.month + requestData['number_of_extended_months']
        numberOfDaysInMonth = monthrange(date.year, date.month)
        tripDays = int(requestData['trip_days'])
        finalHotelsList = []
        graphList = []
        print("below is type")
        flightObj = flightList[0]['outbounddate']
        # print(flightObj)
        # print(type(flightObj))
        # print("DOPES THIS WORKWE:@??????? HELLO HELLO HELLO AYE AYE AYE FR FR FR ")
        # print(list(hotelModels.HotelDetail.objects.filter(destination_code=requestData['destination_code']).values_list('code', flat=True))[0])
        # print(list(hotelModels.HotelDetail.objects.filter(destination_code=requestData['destination_code']).values_list('code', flat=True)))
        hotelCodes = list(hotelModels.HotelDetail.objects.filter(destination_code=requestData['destination_code']).values_list('code', flat=True))
        # hotelListDivided = np.array_split(hotelCodes, len(flightList))
        print("below is hotelCodes")
        print(len(hotelCodes))
        divideBy = int(int(len(hotelCodes)) / (int(len(flightList))))
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
                # print(data)
                try:
                    result = requests.post(
                        liveHotelsPricingURL,
                        json=data,
                        headers=headers_dict
                    )
                    print(data)
                    if (currentHotelListSection == len(hotelListDivided)-1):
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
                        if(hotelBedsList is not None):
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
                                        if len(images)>0:
                                            hotel_images = [HOTELS_PHOTOS_BASE_URL + image['image_url'] for image in images.values('image_url')]
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
    
    def findBestPackages(self, offlineFlightResults, hotelDeals):
        bestPackagesList = []
        # print("number of offline flight results=========", len(offlineFlightResults))
        # print("number of hotelDeals results=========", len(hotelDeals))
        # return []
        # print("below is a hotel object")
        # print(hotelDeals[0])
        # print("below is a flight object")
        # print(offlineFlightResults[0])
        number = 0
        # TODO: Use the array that is longer to iterate through
        for hotel in hotelDeals:
            print("hotel DATES")
            print(hotel['outbounddate'], " TO ", hotel['inbounddate'])
        # print("hotel price=======", hotel['price'])
        # print()
        for flight in offlineFlightResults:
            # print("============single details======")
            # print("flight outbounddate=======", flight['outbounddate'])
            # print("flight price=======", flight['price'])
            # print(flight)
            for hotel in hotelDeals:
                # print("hotel price=======", hotel['price'])
                # print()
                if (
                    (flight['outbounddate'] == hotel['outbounddate']) & 
                    (float(hotel['price']) != 0) & 
                    (float(flight['price']) != 0)
                ):
                    number += 1
                    print("match found")
                    print("Total matches")
                    print(number)

                    total_price = float(flight['price']) + (float(hotel['price']))
                    bestPackagesList.append({
                        'outbounddate' : flight['outbounddate'],
                        'inbounddate' : flight['inbounddate'],
                        'flight_price' : flight['price'],
                        'carrier_name' : flight['carrier_name'],
                        'hotel_price' : float(hotel['price']),
                        'tripDays': hotel['tripDays'],
                        'deal_price' : round(total_price, 2),
                        'hotel': hotel['hotel']['hotel'] if hotel['hotel']['hotel'] else [],
                        'images': hotel['hotel']['images'] if hotel['hotel']['images'] else [],
                        'country': flight['country'],
                        'hotel_object': hotel['hotel_object']
                    })
            # break
        print("Below is bestPackages list length")
        print(len(bestPackagesList))
        return bestPackagesList

    def post(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        if user_id:
            userExists = NewUser.objects.filter(id=user_id).all()
            ## user serializer.. will help to log the details for search history
            user = user_serializer.AddFlightsHotelPackageHistory(data = request.data)
            if user.is_valid():
                user.save()
            
            ## flights hotel package serializer
            package_serializer = serializers.FlightsHotelPackageSerializer(data = request.data)
            if package_serializer.is_valid():
                # TODO: Use services.package_service
                offlineFlightData = self.getOfflineFlightsResult(data = request.data)
                # offlineFlightData = []
                hotelDeals = self.getHotelDeals(requestData = request.data, flightList = offlineFlightData)
                finalList = self.findBestPackages(offlineFlightData, hotelDeals)
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
            'autosuggest/v1.0/US/GBP/en-US/?query={}&apiKey={}'\
            .format(airportName, FLIGHTS_API_KEY)
        
        result = requests.get(
            autoSuggestURL
        )

        if (result.status_code == 200):
            jsonData = json.loads(result.text)
            places = jsonData['Places']
            placeId = 'NA'
            if len(places)>0:
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
                        country_code = country['Id'],
                        name = country['Name']
                    )
                    cities_list = []
                    # print("country details=======", country)
                    # for city in country['Cities'][:10]:
                    for city in country['Cities']:
                        airports_list = []
                        city_object = ''
                        try:
                            city_object = models.CityModel.objects.create(
                                city_name = city['Name'],
                                city_code = city['IataCode']
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
                                        country = country_object,
                                        city = city_object,
                                        airport_name = airport['Name'],
                                        airport_code = code
                                    )
                                except Exception as e:
                                    pass
                        if len(airports_list)>0:
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

class GetAirportCode(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('query')
        print("query=========", query)
        if query is not None:
            airports = list(models.AirportModel.objects.filter(
                airport_name__icontains=query
                ).values(
                'airport_name', 'airport_code', 
                'city__city_name', 'city__city_code')[:6])
        else:
            country = request.query_params.get('country')
            airports = list(models.AirportModel.objects.filter(
                country__country_code__icontains=country
            ).values('airport_name', 'airport_code', 
            'city__city_name', 'city__city_code')[:6])
        if (len(airports)>0):
            return Response({
                'list': airports
            }, status=status.HTTP_200_OK)
        else:
            return Response({'list': []}, status=status.HTTP_406_NOT_ACCEPTABLE)

