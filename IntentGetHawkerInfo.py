from flask import Flask, request, make_response, jsonify
import requests
import json

from lxml import html
import urllib.parse as urllib
from urllib.error import HTTPError
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
        
    theXpath2 = '//h2/a/@href' # get text the link
    resultList2 = parser.xpath(theXpath2)
    return resultList1, resultList2    

def processHawkerInfoIntent(req):
    Answer = req["queryResult"]["parameters"]["Answer"]
    if Answer == 'Yes':
        url = 'https://www.thebestsingapore.com/eat-and-drink/the-best-5-hawker-centres-in-singapore/'
        nameList, urlList = getHawkerInfoIntentHandler(url)
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
                        "subtitle": "",
                        "imageUri": "",
                        "buttons": [{"text": "Go to site","postback": urlList[i]}]
                    }
                })
                num = num + 1

            fulfillmentMessage.append({
                    "platform": "slack",
                    "platform": "facebook",
                    "platform": "ACTIONS_ON_GOOGLE"
            })
    else:
        fulfillmentMessage = [
            { "text": {
                "text": ["So would you want to check on other options ?"]}
            }
        ]
        
         
    RichMessages =  {
        # "fulfillmentText": defaultPayload,
        "fulfillmentMessages": fulfillmentMessage

    }

    return make_response(jsonify(RichMessages))
