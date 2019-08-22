from flask import Flask, request, make_response, jsonify
import requests
import json

from lxml import html
import urllib.parse as urllib
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.parse import urlencode


DEBUG_MODE = False


# *****************************
# Hawker Intent Handlers funcs :
# *****************************

def getHawkerInfoIntentHandler(url):
    try:
        page = requests.get(url)
    except HTTPError as e:
        print(e)
        return None
    except URLError as e:
        print('The server could not be found!')

    try:
        parser = html.fromstring(page.content)
    except AttributeError as e:
        return None

    theXpath1 = '//h2//text()' # get text for the THE 5 BEST HAWKER CENTRES IN SINGAPORE
    resultList1 = parser.xpath(theXpath1)
    while ' ' in resultList1:
        resultList1.remove(' ')

    theXpath2 = '//h2/a/@href' # get the link
    resultList2 = parser.xpath(theXpath2)

    theXpath3 = '//ul[2]/li[1]/p/text()' # get the highlights
    resultList3 = parser.xpath(theXpath3)

    return resultList1, resultList2, resultList3

def processHawkerInfoIntent(req):
    intent_name = req["queryResult"]["intent"]["displayName"]
    # Answer = req["queryResult"]["parameters"]["Answer"]
    if (intent_name == "Hawker Info-yes"):
        url = 'https://www.thebestsingapore.com/eat-and-drink/the-best-5-hawker-centres-in-singapore/'
        nameList, urlList, highlights = getHawkerInfoIntentHandler(url)
        if nameList == None:
            fulfillmentMessage = [
                { "text": {
                    "text": ["Error processing information ... Please try again"]}
                }
            ]
        else:
            fulfillmentMessage = []
            num = 1
            for i in range(0, len(nameList)):
                # defaultPayload = "DEFAULT PAYLOAD"
                fulfillmentMessage.append({
                    "card": {
                        "title": nameList[i],
                        "subtitle": highlights[i],
                        "imageUri": "",
                        "buttons": [{"text": "Go to site","postback": urlList[i]}]
                    }
                })
                num = num + 1

            fulfillmentMessage.append({
                    "quickReplies": {
                        "title": "Choose one:",
                        "quickReplies": [
                           "Get Restaurant Info",
                           "Hawker Info",
                           "Top 50 Restaurants"
                         ]
                    },
                    "platform": "slack",
                    "platform": "facebook",
                    "platform": "ACTIONS_ON_GOOGLE"
            })
    elif (intent_name == "Hawker Info-no"):
        if DEBUG_MODE: print("User has cancelled... Redirect to welcome")
        followupEvent = {"name": "WELCOME"}
        return make_response(jsonify({
            "followupEventInput": followupEvent
        }))

        # fulfillmentMessage = [
        #     { "quickReplies": {
        #         "title": "Choose one:",
        #         "quickReplies": [
        #             "Get Restaurant Info",
        #             "Hawker Info",
        #             "Top 50 Restaurants"
        #         ]
        #        },
        #        "platform": "facebook",
        #        "platform": "slack",
        #        "platform": "ACTIONS_ON_GOOGLE"
        #     }
        # ]
    else:
        return make_response(jsonify({
            "fulfillmentMessages": [{
                "quickReplies": {
                    "title": ["Would you like to know which are the best Hawkers in Singapore?"],
                    "quickReplies": [
                        "Yes", "No"
                    ]
                }
            }]
        }))



    RichMessages =  {
        # "fulfillmentText": defaultPayload,
        "fulfillmentMessages": fulfillmentMessage

    }

    return make_response(jsonify(RichMessages))
