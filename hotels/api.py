from django.shortcuts import render
import hashlib
import time
import requests
import json

HOTELS_API_URL = "https://api.test.hotelbeds.com"
HOTELS_API_KEY = "ce0f06ea4efa6d559dd869faae735266"
HOTELS_API_SECRET_KEY = "58a4678b4c"

def createXSignature():
    currentTimeStamp = int(time.time())
    result = HOTELS_API_KEY + HOTELS_API_SECRET_KEY + str(currentTimeStamp)
    result = hashlib.sha256(result.encode()).hexdigest()
    return result

def getContentApi():
    getListofCountriesUrl = HOTELS_API_URL + '/hotel-content-api/1.0/locations/countries?fields=all&language=ENG'
    headers_dict = {
        "Api-key": "ce0f06ea4efa6d559dd869faae735266",
        "X-Signature": createXSignature(),
        "Accept": "application/json",
        "Accept-Encoding":"gzip",
        "Content-Type": "application/json"
    }

    result = requests.get(
        getListofCountriesUrl,
        headers=headers_dict
    )