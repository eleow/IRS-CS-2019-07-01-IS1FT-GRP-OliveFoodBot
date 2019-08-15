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
DEFAULT_LOCATION = "Singapore"
DEBUG_MODE = False

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

    slackBlocks = []
    dict_stars = {
        "0.0": "stars_0",
        "1.0": "stars_1",
        "1.5": "stars_1_half",
        "2.0": "stars_2",
        "2.5": "stars_2_half",
        "3.0": "stars_3",
        "3.5": "stars_3_half",
        "4.0": "stars_4",
        "4.5": "stars_4_half",
        "5.0": "stars_5"
    }

    # # Slot filling check for required parameters
    # invalid = validateParameters(req["queryResult"]["parameters"])
    # if (invalid != None):
    #     return make_response(jsonify(invalid))


    # # Slot filling passed
    RestaurantNameRaw = req["queryResult"]["parameters"]["restaurantName"]
    Location = req["queryResult"]["parameters"].get("location")
    if (Location == None or Location == ""): Location = DEFAULT_LOCATION

    address = getLocationAsString(Location)
    # address = Location if isinstance(Location, str) else Location.get("street-address")
    # if (address == "" or address == None): address = Location.get("city")
    # if (address == "" or address == None): address = Location.get("country")
    # # if (address == "" or address == None): address = Location.get("business-name")
    # if (address == "" or address == None): address = DEFAULT_LOCATION
    # if (address.lower() in ["anywhere", "anything"]): address = DEFAULT_LOCATION    # quick-fix for bug

    RestaurantName = RestaurantNameRaw.replace(" ","-")
    # RestaurantName = ''.join(e for e in RestaurantNameRaw if e.isalnum()) + "-Singapore"   # remove non-alnum
    results = getRestaurantInfoIntentHandler(RestaurantName, address, 1 if address != DEFAULT_LOCATION else 5)

    if (results == None):
        fulfillmentMessage = [
            { "text": {
                "text": ["No businesses for " + RestaurantNameRaw + " in " + address + " found."]}
            }
        ]
    else:
        fulfillmentMessage = []
        fulfillmentMessage.append({
            "text": {
                "text": ["Here are your results for " + RestaurantNameRaw + " located in " + address]
            }
        })

        emojiArr = ["🥣","🍝","🍲", "🍜","😋","😊","😁"]
        emoji = random.choice(emojiArr)
        resultText = "Here are your results for *" + RestaurantNameRaw + "* located in *" + address + "* " + emoji
        resultText = resultText + "\nClick the restaurant name to get more info and click on address to get directions"

        slackBlocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": resultText
            }
        })
        slackBlocks.append({"type": "divider"})


        num = 1
        for r in results:
            # subTitle = "Address:\t %s. \nPhone:\t %s. \nPrice Range:\t %s. \nOpening Hours:\t %s. \nCategory:\t %s." % (r["address"], r["phone"], r["price_range"], r["hours"], r["category"])
            subTitle = "Address:\t %s. \nPhone:\t %s. \nPrice Range:\t %s. \nCategory:\t %s. \n%s" % (r["address"], r["phone"], r["price_range"], r["category"], r["hours"])
            title = r["name"]
            if len(results) != 1: title = str(num) + ". " + title
            # defaultPayload = "DEFAULT PAYLOAD"
            fulfillmentMessage.append({
                "card": {
                    "title": title, "subtitle": subTitle,
                    "imageUri": "",
                    "buttons": [{"text": "Go to site","postback": r["website"]}]
                }
            })

            # form google directions url based on address
            google_destination = urllib.quote(r["address"].replace(" ", "+"))
            print(google_destination)
            google_directions_url = "https://www.google.com/maps/dir/?api=1&destination="+ google_destination

            # slack specific output
            # slackText = "*<%s|%s>*\n%s\n%s\nPhone: %s\n*%s*" % (r["website"], title, r["price_range"], r["address"], r["phone"], r["hours"])
            slackText1 = "*<%s|%s>*\n" %(r["website"], title)
            if (r["price_range"] != "N/A"): slackText1 = slackText1 + "%s" % (r["price_range"])
            if (r["price_range"] != "N/A" and r["category"] != ""): slackText1 = slackText1 + " • "
            if (r["category"] != ""): slackText1 = slackText1 + "%s\n" % (r["category"])
            if (r["address"] != ""): slackText1 = slackText1 + "<%s|%s>\n" % (google_directions_url, r["address"])
            if (r["phone"] != ""): slackText1 = slackText1 + "%s\n" % (r["phone"])

            slackBlocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": slackText1
                },
                "accessory": {
                    "type": "image",
                    "image_url": r["image"],
                    "alt_text": "Thumbnail"
                }
            })
            # slackBlocks.append({
            #     "type": "context",
            #     "elements": [
            #         {
            #             "type": "image",
            #             "image_url": "https://f03acdae.ngrok.io/static/yelp_stars/web_and_ios/regular/regular_2_half@2x.png",
            #             "alt_text": "Location Pin Icon"
            #         }
            #     ]
            # })
            star_url = dict_stars.get(str(r["rating"]), None)
            if (star_url != None):
                slackBlocks.append({
                    "type": "image",
                    "image_url": "https://e67cda03.ngrok.io/static/yelp_stars/" + star_url + ".png",
                    "alt_text": "stars"
                })
            slackBlocks.append({"type": "divider"})
            num = num + 1


    RichMessages =  {
        # "fulfillmentText": defaultPayload,
        "fulfillmentMessages": fulfillmentMessage,
        "payload": {
            "slack": {
                "attachments": [{
                    "blocks": slackBlocks
                }]
            },
        }
    }

    # Return the Restaurant Information
    return make_response(jsonify(RichMessages))


def processRestaurantInfoIntents(req):
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
        temp1 = yelp_query_api(restaurantName, location, num_results=num_results, debug=False)
    except HTTPError as error:
        if (DEBUG_MODE): print("HTTP ERROR! " + error.code)
        return None

    if (temp1 == None): return None
    else:
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


