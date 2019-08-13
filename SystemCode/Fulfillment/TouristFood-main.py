from flask import Flask, request, make_response, jsonify
import requests
import json

from lxml import html

import builtins as exceptions
from time import sleep
# import re,urllib.parse as urllib
import argparse

from IntentGetRestaurantInfo import processRestaurantInfoIntents
from IntentGetHawkerInfo import processHawkerInfoIntent

#from flask_assistant import ask, tell, event, build_item

app = Flask(__name__)


# *****************************
# WEBHOOK MAIN ENDPOINT : START
# *****************************
@app.route('/', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    intent_name = req["queryResult"]["intent"]["displayName"]

    if ("GetRestInfo" in intent_name):
        return processRestaurantInfoIntents(req)
    # if intent_name == "GetRestInfo-Entry":
    #     return processRestaurantInfoIntent(req)
    # elif intent_name == "GetRestInfo-Location":
    #     return processRestaurantInfoLocationIntent(req)
    # elif "GetRestInfo-Confirm" in intent_name:
    #     return processRestaurantInfoConfirmIntent(req)
    # elif intent_name == "GetRestInfo-Confirm-Yes":
        # return processRestaurantInfoConfirmIntent(req)

    elif intent_name == "Hawker Info":
        return processHawkerInfoIntent(req)
    else:
        fulfillmentText = "Unable to find a matching intent. Try again."
        # return make_response(jsonify({'fulfillmentText': RichMessages}))
        return make_response(jsonify({
            "fulfillmentText": fulfillmentText,
            "fulfillmentMessages": [
                {
                  "text": {"text": ["Sorry, I am unable to understand. Please choose one of the options below:"]}
                },
                {
                    "quickReplies": {"quickReplies": ["Get Restaurant Info", "Top 50 Restaurants", "Cheap and Good Food"]}
                }
            ]
        }))

# ***************************
# WEBHOOK MAIN ENDPOINT : END
# ***************************
if __name__ == '__main__':
   app.run(debug=True, host='0.0.0.0', port=5000)
