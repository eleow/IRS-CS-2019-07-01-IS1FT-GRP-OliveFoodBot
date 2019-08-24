#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 14:03:15 2019

@author: meiying

"""

from flask import make_response, jsonify
from yelpAPIHelper import yelp_request
from richMessageHelper import displayResults_slack
import random

YELP_API_KEY = "rG5TOrDyCq0G-lIelg9XzKfBcSNrc2F7zsa3C99Nray3q_-Wz8YU1Jdi1rAu7-gSQwdKCuZA0b9GXCp5xMImW9_dxQo_9ib4OAJ-PXRyqPGakfQD8WHL8BX7uDNJXXYx"
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'

DEBUG_MODE = False
public_url = ""

def getPopularDiningInfoIntentHandler(PARAMETERS):
    business_data = yelp_request(API_HOST, SEARCH_PATH, YELP_API_KEY, PARAMETERS, debug=DEBUG_MODE)
    biz_array = []
    if business_data["total"] > 0:
        for biz in business_data["businesses"]:
            #bizDict["hours"].append("Open Now" if biz.get("hours", None) != None and biz["hours"][0]["is_open_now"] else "Closed")
            biz_array.append({
                "name": biz.get("name", ""),
                "phone": biz.get("phone", "N/A"),
                "address": ", ".join(biz["location"]["display_address"]),
                "price_range": biz.get("price", "N/A"),
                "category": ", ".join(map(lambda x: x["alias"], biz["categories"])),
                "website": biz.get("url", "N/A"),
                "image": biz.get("image_url", "N/A"),
                "review_count": biz.get("review_count", "N/A"),
                "rating": biz.get("rating", "N/A"),
                "is_closed": biz.get("is_closed", "")
            })
            #bizDict["photo"].append(biz["photos"][0] if (biz.get("photos", None) != None and len(biz["photos"])>=1) else None)
    return biz_array

def processPopularDiningIntent(results, header):
    
    if len(results) > 0:
        rich_messages = displayResults_slack(results, public_url, header, default_header_msg = None, use_is_closed=True)
    else:
        rich_messages = {"fulfillmentText": "There are no results. Please try another search."}
    return make_response(jsonify(rich_messages))

def hawkerCentreIntentHandler(req, url):
    global public_url
    public_url = url
    
    for context in req["queryResult"]["outputContexts"]:
        if "session_var" in context["name"]:
            dining = context["parameters"].get("hawkerCentre", None)
            limit = int(context["parameters"].get("number", None)) # must be integer
            break
    if dining == None:    
        dining = req["queryResult"]["parameters"].get("hawkerCentre", None)    
    if limit == None:
        limit = int(req["queryResult"]["parameters"].get("number", None))
    PARAMETERS = {"term": dining, "limit": limit, "sort_by": "rating", "price":1, "location": "Singapore"}  
    results = getPopularDiningInfoIntentHandler(PARAMETERS)
    emojiArr = ["🥣","🍝","🍲", "🍜","😋","😊","😁"]
    emoji = random.choice(emojiArr)
    resultText = "Here are some of the most popular " + dining + "s in Singapore!" + emoji 
    return processPopularDiningIntent(results, resultText)

def restaurantIntentHandler(req, url):
    global public_url
    public_url = url
    
    budgetDict = {"moderatelypriced": 2, "expensive": 3, "veryexpensive": 4}
    
    for context in req["queryResult"]["outputContexts"]:
        if "session_var" in context["name"]:
            dining = context["parameters"].get("restaurant", None)
            cuisine = context["parameters"].get("cuisine", None)
            budget = context["parameters"].get("budget", None)
            limit = int(context["parameters"].get("number", None))
            break
    if dining == None:
        dining = req["queryResult"]["parameters"].get("restaurant", None)  
    if cuisine == None:
        cuisine = req["queryResult"]["parameters"].get("cuisine", None)     
    if budget == None:
        budget = req["queryResult"]["parameters"].get("budget", None)
    if limit == None:
        limit = int(req["queryResult"]["parameters"].get("number", None))

    PARAMETERS = {"term": dining, "categories": cuisine, "limit": limit, "sort_by": "rating", "price":budgetDict[budget.replace(" ", "")], "location": "Singapore"}
    results = getPopularDiningInfoIntentHandler(PARAMETERS)
    #print(results)
    emojiArr = ["🥣","🍝","🍲", "🍜","😋","😊","😁"]
    emoji = random.choice(emojiArr)
    resultText = "Here's a list of popular " + dining + "s in Singapore!" + emoji 
    return processPopularDiningIntent(results, resultText)

def foodItemIntentHandler(req, foodItem, url, limit = 5):
    global public_url
    public_url = url
    
    PARAMETERS = {"term": foodItem, "limit": limit, "sort_by": "rating", "location": "Singapore"}
    results = getPopularDiningInfoIntentHandler(PARAMETERS)
    return processPopularDiningIntent(results, "Popular eateries selling " + foodItem)
