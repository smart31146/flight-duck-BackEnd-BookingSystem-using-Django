from calendar import monthrange
import datetime
from hotels import models as hotel_models


def find_best_packages(flight_results: list, hotel_deals: list) -> list:
    best = []
    for flight in flight_results:
        for hotel in hotel_deals:
            if (
                (flight['outbounddate'] == hotel['outbounddate']) & 
                (float(hotel['price']) != 0) & 
                (float(flight['price']) != 0)
            ):
                total_price = float(flight['price']) + (float(hotel['price']))
                best.append({
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

    return best

def get_flights(payload: dict) -> list:
    # flights = []
    # date = datetime.datetime.strptime(payload['outbound_date'], '%Y-%m-%d')
    # num_of_months = date.month + payload['number_of_extended_months']
    # num_of_days = monthrange(date.year, date.month)
    # trip_days = int(payload['trip_days'])
    # for current_month in range(date.month, num_of_months+1):
    #     if current_month<10:
    #         current_month = "0"+str(current_month) # TODO: Try another method
    #     start_day = 1
    #     if date.month == int(current_month):
    #         start_day = int(current_month)
    #     for day in range(start_day, num_of_days[1]+1):
    #         departure_date : str
    #         return_date : str
    #         current_month_inc = False
    #         day = int(day) # TODO: Try avoid the constant casts
    #         return_day = int(day+trip_days)
    #         current_month = int(current_month)
    #         if day<10:
    #             day = "0"+str(day)
    #         if int(current_month)<10:
    #             current_month = "0"+str(current_month)
    #         # TODO: Fix the disgusting line below
    #         departure_date = str(date.year) + "-" + str(current_month) + "-" + str(day)
    #         if return_day>num_of_days[1]:
    #             return_day = return_day-num_of_days[1]
    #             current_month = int(current_month)+1
    #             current_month_inc = True
    #             if current_month<10:
    #                 return_day = "0"+str(return_day)
    #             return_date = str(date.year) + "-" + str(current_month) + "-" + str(return_day)

    #             country_name = hotel_models.HotelCountry.objects.filter(country_code=payload['country']).first()

    #             url = f''
                # url = '{0}browseroutes/v1.0/{1}/{2}/en-US'

        
    pass