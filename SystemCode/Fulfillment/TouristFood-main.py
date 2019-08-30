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
from IntentGetDiningInfo import hawkerCentreIntentHandler, restaurantIntentHandler, foodItemIntentHandler
from IntentWhatIs import whatisIntentHandler
from richMessageHelper import displayWelcome_slack


API_KEY = 'rG5TOrDyCq0G-lIelg9XzKfBcSNrc2F7zsa3C99Nray3q_-Wz8YU1Jdi1rAu7-gSQwdKCuZA0b9GXCp5xMImW9_dxQo_9ib4OAJ-PXRyqPGakfQD8WHL8BX7uDNJXXYx'
ENDPOINT = 'https://api.yelp.com/v3/businesses/search'
HEADERS = {'Authorization':'bearer %s' %API_KEY}

global RUN_NGROK
RUN_NGROK = True
import sys
if len(sys.argv) == 2:
  RUN_NGROK = False if sys.argv[1] != '1' else True



# import colorama
# colorama.init()

# For running ngok directly from python
public_url = ""
if (RUN_NGROK):
    from pyngrok import ngrok
    from os.path import abspath, dirname, join, realpath, isfile

    dir_path = dirname(realpath(__file__))
    ngrok.DEFAULT_CONFIG_PATH = join(dir_path, "ngrok.yml")
    # ngrok.DEFAULT_NGROK_PATH = join(dir_path, "ngrok.exe")
    # tunnels = ngrok.get_tunnels(ngrok_path=join(dir_path, "ngrok.exe"))
    tunnels = ngrok.get_tunnels()
    if (len(tunnels) == 0):
        public_url = ngrok.connect(port=5000, proto="http")
    else:
        public_url = tunnels[0].public_url
    print("--------------------------------------------------------------------")
    print(" Flask will be run from ngrok")
    print("--------------------------------------------------------------------")
else:
    public_url = "https://olivefoodbot.herokuapp.com" # Use heroku url
    print("--------------------------------------------------------------------")
    print(" Flask will be run from Heroku")
    print("--------------------------------------------------------------------")

print(" * PUBLIC URL: " + public_url)
app = Flask(__name__)


# *****************************
# WEBHOOK MAIN ENDPOINT : START
# *****************************
from flask import render_template
@app.route('/', methods=['POST', 'GET'])
def webhook():
    if (request.method == 'GET'):
        message = "Flask Webhook is running @ " + public_url
        return render_template('index.html', message=message, img="/static/olive.png")

    elif (request.method == 'POST'):
        req = request.get_json(silent=True, force=True)
        intent_name = req["queryResult"]["intent"]["displayName"]
        action = req["queryResult"].get("action", None)
        foodItem = req["queryResult"]["parameters"].get("foodItem", None)
        hawkerCentreIntents = ["GetHawkerCentre", "GetHawkerCentreComplete"]
        restaurantIntents = ["GetRestaurant", "GetRestaurantComplete", "GetRestaurantCuisineFirst",
                             "GetRestaurantBudgetFirst", "GetRestaurantNumberFirst",
                             "GetRestaurantCuisineBudgetFirst", "GetRestaurantCuisineNumberFirst",
                             "GetRestaurantBudgetNumberFirst"]
        # restaurantIntentsConfirmation = ["UserRepliesNumberRestaurant"]

        if ("GetRestInfo" in intent_name):
            return processRestaurantInfoIntents(req, public_url)

        elif ("Hawker Info" in intent_name):
            return processHawkerInfoIntent(req)

        elif action in ["WELCOME"] or "Default Welcome Intent" in intent_name:
            wasRedirected = (req["queryResult"].get("outputContexts") != None and any("welcome" in d["name"] for d in req["queryResult"].get("outputContexts")))
            additional_header = None if not wasRedirected else "I am sorry, but I could not understand. Try rephasing your query."
            return make_response(jsonify(displayWelcome_slack(public_url, additional_header = additional_header)))

        elif (action in hawkerCentreIntents):
            return hawkerCentreIntentHandler(req, public_url)

        elif (action in restaurantIntents):
            return restaurantIntentHandler(req, public_url)

        # replaced knowledge-base intent with explicit intent for more control
        elif (intent_name == "WhatIsDish"):
            return whatisIntentHandler(req, public_url)

        elif foodItem != None:
            print(foodItem)
            return foodItemIntentHandler(req, foodItem, public_url)

        else:
            # Cannot understand. Just redirect to welcome screen
            followupEvent = {"name": "WELCOME",
                "parameters": {
                    "unknown": True
                }
            }
            return make_response(jsonify({"followupEventInput": followupEvent}))



# ***************************
# WEBHOOK MAIN ENDPOINT : END
# ***************************

import os
#from pml import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=True, host='0.0.0.0', port=port)
