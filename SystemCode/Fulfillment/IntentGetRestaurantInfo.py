from flask import Flask, request, make_response, jsonify
import requests
import json

from lxml import html
import re
import urllib.parse as urllib
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.parse import urlencode
import random
# import pprint

from yelpAPIHelper import yelp_query_api
from richMessageHelper import displayResults_slack
DEFAULT_LOCATION = "Singapore"
DEBUG_MODE = False
public_url = ""


# **********************
# UTIL FUNCTIONS : END
# **********************
def validateParameters(params):
    returnText = []
    followupEvent = {}
    passRestaurantName = True

    RestaurantName = params["restaurantName"]
    if (RestaurantName == "" or RestaurantName.lower() in ["hi", "hello", "how are you"]):
        restNameArray = ["Please enter a restaurant", "Which restaurant would that be?", "Which restaurant are you interested in?", "Could you tell me the name of the restaurant that you are interested in?"]
        returnText.append(random.choice(restNameArray))
        passRestaurantName = False

        # Invoke this event if it fails restaurant-name check
        # TODO
        followupEvent = {

        }

    if (passRestaurantName):
        Location = params.get("location", DEFAULT_LOCATION)
        Country = Location.get("country", None) if isinstance(Location, dict) else None
        if (Location == "" or (Country != None and Country != "" and Country != "Singapore")):
            # Invoke this event if it fails location check
            returnText.append("Redirecting to GetRestInfo-Location")
            if DEBUG_MODE: print("... Redirecting to GetRestInfo-Location")
            followupEvent = {
                "name": "actions_intent_restaurantInfo_getLocation",
                "parameters": {
                    "restaurantName": RestaurantName
                }
            }

    if (len(returnText) == 0): return None
    else:
        return {
            "fulfillmentMessages": [{
                "text" : {
                    "text": returnText  # Note that this will not be used if there is followupEventInput
                }
            }],
            "followupEventInput": followupEvent
        }

def processRestaurantInfoConfirmIntent(req):
    p = req["queryResult"]["parameters"]
    RestaurantName = p.get("restaurantName")
    Location = p.get("location", DEFAULT_LOCATION)
    address = getLocationAsString(Location)

    followupEvent = {}
    returnText = []

    intent_name = req["queryResult"]["intent"]["displayName"]

    if (intent_name == "GetRestInfo-Confirm"):
        if DEBUG_MODE: print("All parameters filled... We will seek user's confirmation")
        confirmArr = [
            "Okay great. I will get the top results for " + RestaurantName + " in " + address + "?",
            "Okay. I will get you details on " + RestaurantName + " in " + address + ". Is that right?",
            "Got it. " + RestaurantName + " in " + address + "?"]
        returnText.append(random.choice(confirmArr))

        return make_response(jsonify({
            "fulfillmentMessages": [
                {
                    "quickReplies": {
                        "title": returnText,
                        "quickReplies": [
                            "Yes", "No"
                        ]
                    }
                }
            ]
        }))

    # If it's yes, we forward back to restaurntInfo with all entities filled
    elif (intent_name == "GetRestInfo-Confirm-yes"):
        if DEBUG_MODE: print("User has confirmed... Get results for user now")
        # By this stage, everything should be filled up. Just forward back to restaurantInfo intent
        followupEvent = {
            "name": "actions_intent_restaurantInfo_execute",
            "parameters": {
                "restaurantName": RestaurantName,
                "location": Location
            }
        }

        return make_response(jsonify({
            "followupEventInput": followupEvent
        }))

    # If it's no, we forward back to our default welcome
    else:
        if DEBUG_MODE: print("User has cancelled... Redirect to welcome")
        followupEvent = {"name": "WELCOME"}
        return make_response(jsonify({
            "followupEventInput": followupEvent
        }))

def processRestaurantInfoLocationIntent(req):
    followupEvent = {}
    returnText = []


    # Slot filling check for required parameters
    p = req["queryResult"]["parameters"]
    RestaurantName = p.get("restaurantName")
    bNoPreferredLocation = p.get("RestaurantNoPreferredLocation", "false").lower()

    if (bNoPreferredLocation in ['true', 'yes', '1']):
        # Passed location check, redirect to next intent
        if (DEBUG_MODE): print("Passed location check (No preferred Location). Redirect to GetRestInfo-Confirm")
        followupEvent = {
            "name": "actions_intent_restaurantInfo_confirm",
            "parameters": {
                "restaurantName": RestaurantName,
                "location": DEFAULT_LOCATION
            }
        }
    else:
        # Slot validation check for Location
        Location = p.get("location", DEFAULT_LOCATION)
        Country = Location.get("country", None) if isinstance(Location, dict) else None
        if (Location == ""):
            locationArray = [
                "Okay, " + RestaurantName + " at which location in Singapore?",
                "Sure. I will get you more details on " + RestaurantName + ". Any preferred location?",
                "Alright. Let's get details on " + RestaurantName + ". Any preferred location?"
            ]
            returnText.append(random.choice(locationArray)) # Failed validation - Ask user to try again

        elif ( Country != None and Country != "" and Country != "Singapore"):
            countryArray = [
                "I'm sorry, we cater only to food found in Singapore and not " + Country,
                "Oops! " + Country + " is not supported!"
            ]
            returnText.append(random.choice(countryArray) + ". Please enter a valid location in Singapore") # Failed validation - Ask user to try again
        else:
            # Passed location check, redirect to next intent
            if (DEBUG_MODE): print("Passed location check. Redirect to GetRestInfo-Confirm")
            followupEvent = {
                "name": "actions_intent_restaurantInfo_confirm",
                "parameters": {
                    "restaurantName": RestaurantName,
                    "location": Location
                }
            }

    return make_response(jsonify({
        "fulfillmentMessages": [{
            "text" : {
                "text": returnText  # Note that this will not be used if there is followupEventInput
            }
        }],
        "followupEventInput": followupEvent
    }))



def processRestaurantInfoEntryIntent(req):
    followupEvent = {}

    # Slot filling check for required parameters
    invalid = validateParameters(req["queryResult"]["parameters"])
    if (invalid != None):
        return make_response(jsonify(invalid))


    # Slot filling passed
    RestaurantNameRaw = req["queryResult"]["parameters"]["restaurantName"]
    Location = req["queryResult"]["parameters"].get("location")
    if (Location == None or Location == ""): Location = DEFAULT_LOCATION

    # address = getLocationAsString(Location)

    # Passed slot check, redirect to next intent
    if (DEBUG_MODE): print("Passed location check. Redirect to GetRestInfo-Confirm")
    followupEvent = {
        "name": "actions_intent_restaurantInfo_confirm",
        "parameters": {
            "restaurantName": RestaurantNameRaw,
            "location": Location
        }
    }

    RichMessages =  {
        "followupEventInput": followupEvent
    }
    return make_response(jsonify(RichMessages))

def processRestaurantInfoExeIntent(req):

    # Slot filling passed
    RestaurantNameRaw = req["queryResult"]["parameters"]["restaurantName"]
    Location = req["queryResult"]["parameters"].get("location")
    if (Location == None or Location == ""): Location = DEFAULT_LOCATION

    address = getLocationAsString(Location)
    RestaurantName = RestaurantNameRaw.replace(" ","-")
    # RestaurantName = ''.join(e for e in RestaurantNameRaw if e.isalnum()) + "-Singapore"   # remove non-alnum
    results = getRestaurantInfoIntentHandler(RestaurantName, address, 1 if address != DEFAULT_LOCATION else 5)

    if (results == None):
        fulfillmentMessage = [
            { "text": {
                "text": ["No businesses for " + RestaurantNameRaw + " in " + address + " found."]}
            }
        ]
        RichMessages = {
             "fulfillmentMessages": fulfillmentMessage
        }
    elif (isinstance(results, int)):
        # Error code. 1 - Exceeded daily-limits calls
        if (results == 1): fulText = "It appears that our magic server is overloaded. Please try again tomorrow"
        else: fulText = "We have ran into an unknown problem. Please try again later."
        RichMessages = {
            "fulfillmentMessages": [
                { "text": {
                    "text": [fulText]
                    }
                }
            ]
        }

    else:
        default_msg = "Here are your results for " + RestaurantNameRaw + " located in " + address

        magArr = ["✨Presto!", "✨Abracadabra!", "✨Swish!", "✨Accio!"]
        mag = random.choice(magArr)
        emojiArr = ["🥣","🍝","🍲", "🍜","😋","😊","😁"]
        emoji = random.choice(emojiArr)
        resultText = mag + " Here are your results for *" + RestaurantNameRaw + "* located in *" + address + "* " + emoji

        # check if results contain businesses in similar categories
        hasOthers = not all(list(map(lambda x: RestaurantNameRaw.lower() in x["name"].lower(), results))[1:])
        if (hasOthers):
            resultText = resultText + "\nI have also included restaurants in similar categories."

        RichMessages = displayResults_slack(results, public_url, resultText, default_msg)

    # Return the Restaurant Information
    return make_response(jsonify(RichMessages))


def processRestaurantInfoIntents(req, url):
    global public_url
    public_url = url

    intent_name = req["queryResult"]["intent"]["displayName"]
    if DEBUG_MODE: print("!!!! " + intent_name)

    if intent_name == "GetRestInfo-Entry":
        return processRestaurantInfoEntryIntent(req)
    elif intent_name == "GetRestInfo-Exe":
        return processRestaurantInfoExeIntent(req)
    elif intent_name == "GetRestInfo-Location":
        return processRestaurantInfoLocationIntent(req)
    elif "GetRestInfo-Confirm" in intent_name:
        return processRestaurantInfoConfirmIntent(req)



def getRestaurantInfoIntentHandler(restaurantName, location=DEFAULT_LOCATION, num_results=5):
    """
    Use Yelp APIs to get restaurant details
    """

    try:
        temp1 = yelp_query_api(restaurantName, location, num_results=num_results, debug=DEBUG_MODE)
    except HTTPError as error:
        if (DEBUG_MODE): print("HTTP ERROR! " + error.code)
        return None

    if (temp1 == None): return None
    elif (isinstance(temp1, int)):
        return temp1
    elif (isinstance(temp1, list)):
        query_result_array = []
        for t in temp1:
            query_result_array.append({
                "hours": "Open Now" if t.get("hours", None) != None and t["hours"][0]["is_open_now"] else "Closed",
                "name": t.get("name", ""),
                "phone": t.get("phone", "N/A"),
                "address": ", ".join(t["location"]["display_address"]),
                "price_range": t.get("price", "N/A"),
                "category": ", ".join(map(lambda x: x["alias"], t["categories"])),
                "website": t.get("url", "N/A"),
                "image": t.get("image_url", ""),
                "review_count": t.get("review_count", "N/A"),
                "rating": t.get("rating", "N/A"),
                "photo": t["photos"][0] if (t.get("photos", None) != None and len(t["photos"])>=1) else None
            })

    # return infoCount, website, restName, address, phone, category, price_range, officeHours, take_out, delivery, reservation
    return query_result_array

def getLocationAsString(Location):
    address = Location if isinstance(Location, str) else Location.get("street-address")
    if (address == "" or address == None): address = Location.get("city")
    if (address == "" or address == None): address = Location.get("country")
    if (address == "" or address == None): address = Location.get("business-name")
    if (address == "" or address == None): address = DEFAULT_LOCATION
    if (address.lower() in ["anywhere", "anything"]): address = DEFAULT_LOCATION    # quick-fix for bug
    return address


