#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 14:03:15 2019

@author: meiying

"""

from flask import make_response, jsonify
from yelpAPIHelper import yelp_request
from richMessageHelper import displayResults_slack

YELP_API_KEY = "rG5TOrDyCq0G-lIelg9XzKfBcSNrc2F7zsa3C99Nray3q_-Wz8YU1Jdi1rAu7-gSQwdKCuZA0b9GXCp5xMImW9_dxQo_9ib4OAJ-PXRyqPGakfQD8WHL8BX7uDNJXXYx"
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'

DEBUG_MODE = False
public_url = ""

def getPopularDiningInfoIntentHandler(PARAMETERS):
    business_data = yelp_request(API_HOST, SEARCH_PATH, YELP_API_KEY, PARAMETERS, debug=DEBUG_MODE)
    print(business_data)
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
        rich_messages = {"fulfillmentText": "no results were found."}
    return make_response(jsonify(rich_messages))

def hawkerCentreIntentHandler(req, url):
    global public_url
    public_url = url
    
    for context in req["queryResult"]["outputContexts"]:
        if "session_var" in context["name"]:
            dining = context["parameters"].get("hawkerCentre", None)
            limit = context["parameters"].get("number", None)
            break
    if dining == None:    
        dining = req["queryResult"]["parameters"]["hawkerCentre"]    
    if limit == None:
        limit = req["queryResult"]["parameters"]["number"]
    
    PARAMETERS = {"term": dining, "limit": limit, "sort_by": "rating", "price":1, "location": "Singapore"}  
    results = getPopularDiningInfoIntentHandler(PARAMETERS)
    return processPopularDiningIntent(results, "Popular " + str(dining) + "s")

def restaurantIntentHandler(req, url):
    global public_url
    public_url = url
    
    budgetDict = {"mid-range": 2, "expensive": 3, "veryexpensive": 4}
    
    for context in req["queryResult"]["outputContexts"]:
        if "session_var" in context["name"]:
            dining = context["parameters"]["hawkerCentre"]
            cuisine = context["parameters"]["cuisine"]
            budget = context["parameters"]["budget"]
            limit = context["parameters"]["number"]
            break
    if len(dining) == 0:
        dining = req["queryResult"]["parameters"]["restaurant"]  
    if len(cuisine) == 0:
        dining = req["queryResult"]["parameters"]["cuisine"]     
    if len(budget) == 0:
        limit = req["queryResult"]["parameters"]["budget"]
    if len(limit) == 0:
        limit = req["queryResult"]["parameters"]["number"]    

    PARAMETERS = {"term": dining, "categories": cuisine, "limit": limit, "sort_by": "rating", "price":budgetDict[budget.replace(" ", "")], "location": "Singapore"}
    results = getPopularDiningInfoIntentHandler(PARAMETERS)
    #print(results)
    return processPopularDiningIntent(results, "Popular " + str(dining) + "s")

def foodItemIntentHandler(req, url):
    global public_url
    public_url = url
    
    foodItem = [context["parameters"]["foodItem"] for context in req["queryResult"]["outputContexts"] if "session_var" in context["name"]].pop()
    PARAMETERS = {"term": foodItem, "limit": limit, "sort_by": "rating", "location": "Singapore"}
    results = getPopularDiningInfoIntentHandler(PARAMETERS)
    print(results)
    return processPopularDiningIntent(results, "Popular eateries selling " + str(foodItem))