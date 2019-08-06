from flask import Flask, request, make_response, jsonify
import requests
import json

from lxml import html

import builtins as exceptions
from time import sleep
import re,urllib.parse as urllib
import argparse

#from flask_assistant import ask, tell, event, build_item

app = Flask(__name__)

# **********************
# UTIL FUNCTIONS : START
# **********************

def parse(url):
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

# *****************************
# Intent Handlers funcs : START
# *****************************

def getInfoIntentHandler(RestaurantName):
    """
    Get RestaurantName parameter from dialogflow and call the util function `getWeatherInfo` to get weather info
    """
    url = "https://www.yelp.com/biz/" + RestaurantName + "?osq=Restaurants"

    temp1 = parse(url)

    returnText = ""
    officeHours = ""
    Restname  = ""
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
        RestName = temp1['name']
    else:
        RestName = "No Info"
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

    return infoCount, website, RestName, address, phone, category, price_range, officeHours, take_out, delivery, reservation



# ***************************
# Intent Handlers funcs : END
# ***************************



# *****************************
# WEBHOOK MAIN ENDPOINT : START
# *****************************
@app.route('/', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    intent_name = req["queryResult"]["intent"]["displayName"]


    if intent_name == "Get Restaurant Info":
        RestaurantName = req["queryResult"]["parameters"]["RestaurantName"]
        Rest_Name = RestaurantName

        if RestaurantName != "":
            RestaurantName = RestaurantName.replace(" ","-")
            RestaurantName = RestaurantName + "-Singapore"
            infoCount, website, RestName, address, phone, category, price_range, officeHours, take_out, delivery, reservation = getInfoIntentHandler(RestaurantName)
        else:
            RichMessages = "Restaurant Name is null ..."
            return make_response(jsonify({'fulfillmentText': RichMessages}))
    else:
        RichMessages = "Unable to find a matching intent. Try again."
        return make_response(jsonify({'fulfillmentText': RichMessages}))

    RichMessages =  {
                        "fulfillmentMessages": [
                          {
                            "card": {
                              "title": RestName,
                              "subtitle": address,
                              "imageUri": "",
                              "buttons": [
                                {
                                  "text": "Go to site",
                                  "postback": website
                                }
                               ]
                            },
                            "platform": "slack",
                            "platform": "facebook",
                            "platform": "ACTIONS_ON_GOOGLE"
                        },
                          {
                            "text": {
                              "text": [
                                  "Phone : " + phone + "\n",
                                  "Category : " + category + "\n",
                                  "Price Range : " + price_range + "\n",
                                  "Take out : " + take_out + "\n",
                                  "Delivery : " + delivery + "\n",
                                  "Reservation : " + reservation + "\n",
                                  "Opening Hours : \n" + officeHours
                              ]
                            }
                          }
                        ]
                    }

    # If there are too many no Info then return this messages
    if infoCount > 8:
        RichMessages = "There is no information for the " + Rest_Name
        return make_response(jsonify({'fulfillmentText': RichMessages}))

    # Return the Restaurant Information
    return make_response(jsonify(RichMessages))

# ***************************
# WEBHOOK MAIN ENDPOINT : END
# ***************************

if __name__ == '__main__':
   app.run(debug=True, host='0.0.0.0', port=5000)
