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
    elif ("Hawker Info" in intent_name):
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

import os 
#from pml import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=True, host='0.0.0.0', port=port)
