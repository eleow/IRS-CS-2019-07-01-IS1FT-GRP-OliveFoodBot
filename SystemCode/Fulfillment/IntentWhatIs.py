from flask import make_response, jsonify
import csv
import random
from os import getcwd, chdir
from os.path import abspath, dirname, join, realpath, isfile
from IntentGetDiningInfo import foodItemIntentHandler

# **********************
# UTIL FUNCTIONS : END
# **********************
global foodDic
foodDic = {}

def initiateLookUpTable():
    global foodDic

    dir_path = dirname(realpath(__file__))
    chdir(dir_path)

    with open('_FoodCat.csv', mode='r', encoding="utf-8-sig") as infile:
        reader = csv.reader(infile)
        for row in reader:
            foodDic[row[0].strip().lower()] = row[1]


def whatisIntentHandler(req, public_url):
    returnText = []
    foodItem = req["queryResult"]["parameters"].get("foodItem", None)

    # lazy initialisation of foodDic
    if (not bool(foodDic)): initiateLookUpTable()

    # get food description from foodDic
    foodDescription = foodDic.get(foodItem.strip().lower(), None)
    if (foodDescription == None):
        dunnoArray = [
            "Hmm.. I am not sure what " + foodItem + " is too!",
            "Oops! I don't know what " + foodItem + " is too!"
        ]
        returnText = [random.choice(dunnoArray)]
        return make_response(jsonify({
                "fulfillmentMessages": [
                    {
                        "text" : {
                            "text": returnText
                        }
                    }
                ]
            }))


    else:
        returnText = "*" + foodItem.strip().capitalize() +"*:"
        returnText = returnText + "\n" + foodDescription
        return foodItemIntentHandler(req, foodItem, public_url, pre_header_msg = returnText)




