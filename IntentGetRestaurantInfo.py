from flask import Flask, request, make_response, jsonify
import requests
import json

from lxml import html
import re
import urllib.parse as urllib
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.parse import urlencode
# import pprint

from yelpAPIHelper import yelp_query_api
DEFAULT_LOCATION = "Singapore"
DEBUG_MODE = False

# **********************
# UTIL FUNCTIONS : END
# **********************

def processRestaurantInfoIntent(req):
    RestaurantName = req["queryResult"]["parameters"]["RestaurantName"]

    Location = req["queryResult"]["parameters"].get("Location")
    if (Location == None): Location = DEFAULT_LOCATION

    address = Location if isinstance(Location, str) else Location.get("street-address")
    if (address == "" or address == None): address = Location.get("city")
    if (address == "" or address == None): address = Location.get("country")
    if (address == "" or address == None): address = Location.get("business-name")
    if (address == "" or address == None): address = DEFAULT_LOCATION

    if RestaurantName != "":
        RestaurantName = RestaurantName.replace(" ","-")
        RestaurantName = RestaurantName + "-Singapore"
        results = getRestaurantInfoIntentHandler(RestaurantName, address)

        if (results == None):
            fulfillmentMessage = [
                { "text": {
                    "text": ["No businesses for " + RestaurantName + " in " + address + " found."]}
                }
            ]
        else:
            fulfillmentMessage = []
            num = 1
            for r in results:
                subTitle = "Address:\t %s. \nPhone:\t %s. \nPrice Range:\t %s. \nOpening Hours:\t %s. \nCategory:\t %s." % (r["address"], r["phone"], r["price_range"], r["hours"], r["category"])
                # defaultPayload = "DEFAULT PAYLOAD"
                fulfillmentMessage.append({
                    "card": {
                        "title": str(num) + ". " + r["name"], "subtitle": subTitle,
                        "imageUri": "",
                        "buttons": [{"text": "Go to site","postback": r["website"]}]
                    }
                })
                num = num + 1
    else:
        RichMessages = "Restaurant Name is null ..."


    RichMessages =  {
        # "fulfillmentText": defaultPayload,
        "fulfillmentMessages": fulfillmentMessage

    }

    # Return the Restaurant Information
    return make_response(jsonify(RichMessages))



def getRestaurantInfoIntentHandler(restaurantName, location=DEFAULT_LOCATION, num_results=5):
    """
    Use Yelp APIs to get restaurant details
    """
    # url = "https://www.yelp.com/biz/" + restaurantName + "?osq=Restaurants"
    # temp1 = scrape(url)

    # parser = argparse.ArgumentParser()
    # parser.add_argument('-q', '--term', dest='term', default=DEFAULT_TERM,
    #                     type=str, help='Search term (default: %(default)s)')
    # parser.add_argument('-l', '--location', dest='location',
    #                     default=DEFAULT_LOCATION, type=str,
    #                     help='Search location (default: %(default)s)')
    # input_values = parser.parse_args()

    try:
        temp1 = yelp_query_api(restaurantName, location, num_results=num_results, debug=DEBUG_MODE)
    except HTTPError as error:
        if (DEBUG_MODE): print("HTTP ERROR! " + error.code)
        return None

    if (temp1 == None): return None
    else:
        query_result_array = []
        for t in temp1:
            query_result_array.append({
                "hours": "No Info",
                "name": t.get("name", ""),
                "phone": t.get("phone", ""),
                "address": ", ".join(t["location"]["display_address"]),
                "price_range": t.get("price", ""),
                "category": ", ".join(map(lambda x: x["alias"], t["categories"])),
                "website": t.get("url", "")
            })

    # return infoCount, website, restName, address, phone, category, price_range, officeHours, take_out, delivery, reservation
    return query_result_array

