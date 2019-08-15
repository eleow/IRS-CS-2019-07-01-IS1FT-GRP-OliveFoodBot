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

# For running ngok directly from python
RUN_NGROK = True
public_url = ""
if (RUN_NGROK):
    from pyngrok import ngrok
    from os.path import abspath, dirname, join, realpath, isfile

    dir_path = dirname(realpath(__file__))
    ngrok.DEFAULT_CONFIG_PATH = join(dir_path, "ngrok.yml")
    ngrok.DEFAULT_NGROK_PATH = join(dir_path, "ngrok.exe")
    tunnels = ngrok.get_tunnels(ngrok_path=join(dir_path, "ngrok.exe"))
    if (len(tunnels) == 0):
        public_url = ngrok.connect(port=5000, proto="http")
    else:
        public_url = tunnels[0].public_url
    print(" * PUBLIC URL: " + public_url)

app = Flask(__name__)


# *****************************
# WEBHOOK MAIN ENDPOINT : START
# *****************************
@app.route('/', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    intent_name = req["queryResult"]["intent"]["displayName"]


    if ("GetRestInfo" in intent_name):
        return processRestaurantInfoIntents(req, public_url)
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

# from flask import render_template
# @app.route('/debug')
# def test():
#     message = "TEST DEBUG"
#     return render_template('index.html', message=message, img="/static/yelp_stars/stars_2_half.png")



# ***************************
# WEBHOOK MAIN ENDPOINT : END
# ***************************

import os
#from pml import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=True, host='0.0.0.0', port=port)
