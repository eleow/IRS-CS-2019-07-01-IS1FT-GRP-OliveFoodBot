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

def scrape(url):
    # url = "https://www.yelp.com/biz/frances-san-francisco"
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}
    response = requests.get(url, headers=headers, verify=False).text
    parser = html.fromstring(response)

    raw_name = parser.xpath("//h1[contains(@class,'page-title')]//text()")
    raw_claimed = parser.xpath("//span[contains(@class,'claim-status_icon--claimed')]/parent::div/text()")
    raw_reviews = parser.xpath("//div[contains(@class,'biz-main-info')]//span[contains(@class,'review-count rating-qualifier')]//text()")
    raw_category  = parser.xpath('//div[contains(@class,"biz-page-header")]//span[@class="category-str-list"]//a/text()')
    hours_table = parser.xpath("//table[contains(@class,'hours-table')]//tr")
    details_table = parser.xpath("//div[@class='short-def-list']//dl")
    raw_map_link = parser.xpath("//a[@class='biz-map-directions']/img/@src")
    raw_phone = parser.xpath(".//span[@class='biz-phone']//text()")
    raw_address = parser.xpath('//div[@class="mapbox-text"]//div[contains(@class,"map-box-address")]//text()')
    raw_wbsite_link = parser.xpath("//span[contains(@class,'biz-website')]/a/@href")
    raw_price_range = parser.xpath("//dd[contains(@class,'price-description')]//text()")
    raw_health_rating = parser.xpath("//dd[contains(@class,'health-score-description')]//text()")
    rating_histogram = parser.xpath("//table[contains(@class,'histogram')]//tr[contains(@class,'histogram_row')]")
    raw_ratings = parser.xpath("//div[contains(@class,'biz-page-header')]//div[contains(@class,'rating')]/@title")

    working_hours = []
    for hours in hours_table:
        raw_day = hours.xpath(".//th//text()")
        raw_timing = hours.xpath("./td//text()")
        day = ''.join(raw_day).strip()
        timing = ''.join(raw_timing).strip()
        working_hours.append({day:timing})
    info = []
    for details in details_table:
        raw_description_key = details.xpath('.//dt//text()')
        raw_description_value = details.xpath('.//dd//text()')
        description_key = ''.join(raw_description_key).strip()
        description_value = ''.join(raw_description_value).strip()
        info.append({description_key:description_value})

    ratings_histogram = []
    for ratings in rating_histogram:
        raw_rating_key = ratings.xpath(".//th//text()")
        raw_rating_value = ratings.xpath(".//td[@class='histogram_count']//text()")
        rating_key = ''.join(raw_rating_key).strip()
        rating_value = ''.join(raw_rating_value).strip()
        ratings_histogram.append({rating_key:rating_value})

    name = ''.join(raw_name).strip()
    phone = ''.join(raw_phone).strip()
    address = ' '.join(' '.join(raw_address).split())
    health_rating = ''.join(raw_health_rating).strip()
    price_range = ''.join(raw_price_range).strip()
    claimed_status = ''.join(raw_claimed).strip()
    reviews = ''.join(raw_reviews).strip()
    category = ','.join(raw_category)
    cleaned_ratings = ''.join(raw_ratings).strip()

    if raw_wbsite_link:
        decoded_raw_website_link = urllib.unquote(raw_wbsite_link[0])
        website = re.findall(r"biz_redir\?url=(.*)&website_link",decoded_raw_website_link)[0]
    else:
        website = ''

    if raw_map_link:
        decoded_map_url =  urllib.unquote(raw_map_link[0])
        map_coordinates = re.findall(r"center=([+-]?\d+.\d+,[+-]?\d+\.\d+)",decoded_map_url)[0].split(',')
        latitude = map_coordinates[0]
        longitude = map_coordinates[1]
    else:
        latitude = ''
        longitude = ''

    if raw_ratings:
        ratings = re.findall(r"\d+[.,]?\d+",cleaned_ratings)[0]
    else:
        ratings = 0

    data={'working_hours':working_hours,
        'info':info,
        'ratings_histogram':ratings_histogram,
        'name':name,
        'phone':phone,
        'ratings':ratings,
        'address':address,
        'health_rating':health_rating,
        'price_range':price_range,
        'claimed_status':claimed_status,
        'reviews':reviews,
        'category':category,
        'website':website,
        'latitude':latitude,
        'longitude':longitude,
        'url':url
    }
    return data
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

    # If there are too many no Info then return this messages
    # if infoCount > 8:
    #     RichMessages = "There is no information for the " + RestaurantName
    #     return make_response(jsonify({'fulfillmentText': RichMessages}))

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

        # query_result = {
        #     "hours": "No Info",
        #     "name": temp1["name"],
        #     "phone": temp1["phone"],
        #     "address": ", ".join(temp1["location"]["display_address"]),
        #     "price_range": temp1["price"],
        #     "category": ", ".join(map(lambda x: x["alias"], temp1["categories"])),
        #     "website": temp1["url"]
        # }

    # return infoCount, website, restName, address, phone, category, price_range, officeHours, take_out, delivery, reservation
    return query_result_array

def getRestaurantInfoIntentHandlerByScraping(restaurantName, location=DEFAULT_LOCATION):
    """
    Use Web Scrapping to get restaurant details from Yelp
    """
    url = "https://www.yelp.com/biz/" + restaurantName + "?osq=Restaurants"
    temp1 = scrape(url)

    returnText = ""
    officeHours = ""
    restName  = ""
    phone = ""
    address = ""
    price_range = ""
    category = ""
    website = ""
    reservation = ""
    take_out = ""
    delivery = ""
    infoCount = 0

    if temp1["working_hours"] != []:
        returnText = temp1['working_hours']
        if (len(returnText) > 0):
            for i in range( 0, 7):
                officeHours = officeHours + str(returnText[i]) + "\n"
        else:
            officeHours = "No Info"
            infoCount += 1
    else:
        officeHours = "No Info"
        infoCount += 1
    if temp1["name"] != "":
        restName = temp1['name']
    else:
        restName = "No Info"
        infoCount += 1
    if temp1["phone"] != "":
        phone = temp1['phone']
    else:
        phone = "No Info"
        infoCount += 1
    if temp1["address"] != "":
        address = temp1['address']
    else:
        address = "No Info"
        infoCount += 1
    if temp1["price_range"] != "":
        price_range = temp1['price_range']
    else:
        price_range = "No Info"
        infoCount += 1
    if temp1["category"] != "":
        category = temp1['category']
    else:
        category = "No Info"
        infoCount += 1
    if temp1["website"] != "":
        website = temp1['website']

    if (temp1["info"] != []):
        temp2 = temp1['info']

        if ('Takes Reservations' in temp2[0]):
            reservation = temp2[0]
            reservation = reservation['Takes Reservations']
        else:
            reservation = "No Info"
            infoCount += 1
        if ('Take-out' in temp2[1]):
            take_out = temp2[1]
            take_out = take_out['Take-out']
        else:
            take_out = "No Info"
            infoCount += 1
        if ('Delivery' in temp2[8]):
            delivery = temp2[8]
            delivery = delivery['Delivery']
        else:
            delivery = "No Info"
            infoCount += 1
    else:
        reservation = "No Info"
        take_out = "No Info"
        delivery = "No Info"
        infoCount += 3

    with open("scraped_data-restaurant.json",'w') as fp:
        json.dump(temp1,fp,indent=4)

    return infoCount, website, restName, address, phone, category, price_range, officeHours, take_out, delivery, reservation
