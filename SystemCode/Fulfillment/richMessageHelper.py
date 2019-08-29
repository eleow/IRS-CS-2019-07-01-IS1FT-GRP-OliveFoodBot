import urllib.parse as urllib
import random

def displayWelcome_slack(public_url, default_header_msg = None, additional_header = None):
    fulfillmentMessage = []
    slackBlocks = []

    # Components of introduction message
    introArr = [
        "Hi! I am Olive, your personal foodBot for Singapore food! 👩 ",
        "Hello there! I am Olive, the foodBot for Singapore food 😋 ",
        "👋 I am Olive. How can I help you today? 😊 ",
    ]
    intro = random.choice(introArr) if not additional_header else additional_header

    eg1 = "Find popular eateries"
    eg2 = random.choice(["Din Tai Fung in Orchard", "Swensens in Clementi"])
    eg3 = random.choice(["What is Laksa?", "What is Claypot Rice?"])
    intro2 = "• Recommend a dining place. (eg _%s_)\n• Get a specific restaurant's details such as its location and rating. (eg _%s_)\n• Tell you about specific local food in Singapore. (eg _%s_)\n" % (eg1, eg2, eg3)

    body2 = "Or just click one of the buttons below:"

    header_msg1 = intro + "\n\nHere's a couple of the things I can do:\n" +intro2
    header_msg = header_msg1 + "\n\n" + body2

    # Show header message with a varying image url from 1-9
    img_num = random.randint(1, 9)
    image_url = "https://www.secretfoodtours.com/images/singapore/singapore-tours-" + str(img_num) + ".jpg"
    slackBlocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": header_msg
        },
        "accessory": {
            "type": "image",
            "image_url": image_url,
            "alt_text": "Thumbnail"
        }
    })
    slackBlocks.append({"type": "divider"})

    # Show buttons
    slackBlocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Get eatery information"
                },
                "value": "Get restaurant info"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Find popular hawker centres"
                },
                "value": "Find popular hawker centres"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Find popular restaurants"
                },
                "value": "Find popular restaurants"
            }
        ]
    })


    if (default_header_msg == None): default_header_msg = ''.join([c for c in header_msg1 if c not in ['•','_', '*']])  # remove mrkdown characters
    fulfillmentMessage.append({
        "text": {
            "text": [default_header_msg]
        }
    })

    RichMessages =  {
        # "fulfillmentText": defaultPayload,
        "fulfillmentMessages": fulfillmentMessage,
        "payload": {
            "slack": {
                "attachments": [{
                    "blocks": slackBlocks
                }]
            },
        }
    }
    return RichMessages


def displayResults_slack(results, public_url, header_msg, default_header_msg = None, use_is_popular = False, pre_header_msg = None):
    fulfillmentMessage = []
    slackBlocks = []
    dict_stars = {
        "0.0": "stars_0",
        "1.0": "stars_1",
        "1.5": "stars_1_half",
        "2.0": "stars_2",
        "2.5": "stars_2_half",
        "3.0": "stars_3",
        "3.5": "stars_3_half",
        "4.0": "stars_4",
        "4.5": "stars_4_half",
        "5.0": "stars_5"
    }

    if (default_header_msg == None):
        default_header_msg = ''.join([c for c in header_msg if c not in ['•','_', '*']])  # remove mrkdown characters

    if (pre_header_msg != None):
        slackBlocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": pre_header_msg
            }
        })
        slackBlocks.append({"type": "divider"})
        default_header_msg = ''.join([c for c in pre_header_msg if c not in ['•','_', '*']]) + "\n" + default_header_msg

    fulfillmentMessage.append({
        "text": {
            "text": [default_header_msg]
        }
    })

    header_msg = header_msg + "\nClick the _restaurant name_ to get more info and click on _address_ to get directions"
    slackBlocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": header_msg
        }
    })
    slackBlocks.append({"type": "divider"})

    num = 1
    for r in results:
        if use_is_popular:
            subTitle = "Address:\t %s. \nPhone:\t %s. \nPrice Range:\t %s. \nCategory:\t %s" % (r["address"], r["phone"], r["price_range"], r["category"])
        else:
            subTitle = "Address:\t %s. \nPhone:\t %s. \nPrice Range:\t %s. \nCategory:\t %s. \n%s" % (r["address"], r["phone"], r["price_range"], r["category"], r["hours"])

        title = r["name"]
        if len(results) != 1: title = str(num) + ". " + title # Display count only if there is more than 1 result

        # DEFAULT PAYLOAD
        fulfillmentMessage.append({
            "card": {
                "title": title, "subtitle": subTitle,
                "imageUri": "",
                "buttons": [{"text": "Go to site","postback": r["website"]}]
            }
        })

        # form google directions url based on address
        google_destination = urllib.quote(r["address"].replace(" ", "+"))
        google_directions_url = "https://www.google.com/maps/dir/?api=1&destination="+ google_destination

        # slack specific output
        # slackText = "*<%s|%s>*\n%s\n%s\nPhone: %s\n*%s*" % (r["website"], title, r["price_range"], r["address"], r["phone"], r["hours"])
        slackText1 = "*<%s|%s>*\n" %(r["website"], title)
        if (r["price_range"] != "N/A"): slackText1 = slackText1 + "%s" % (r["price_range"])
        if (r["price_range"] != "N/A" and r["category"] != ""): slackText1 = slackText1 + " • "
        if (r["category"] != ""): slackText1 = slackText1 + "%s\n" % (r["category"])
        if (r["address"] != ""): slackText1 = slackText1 + "<%s|%s>\n" % (google_directions_url, r["address"])
        if (r["phone"] != ""): slackText1 = slackText1 + "%s\n" % (r["phone"])


        if (r["image"] != ""):
            slackBlocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": slackText1
                },
                "accessory": {
                    "type": "image",
                    "image_url": r["image"],
                    "alt_text": "Thumbnail"
                }
            })
        else:
            slackBlocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": slackText1
                }
            })

        star_url = dict_stars.get(str(r["rating"]), None)
        if (star_url != None):
            slackBlocks.append({
                "type": "image",
                "image_url": public_url + "/static/yelp_stars/" + star_url + ".png",
                "alt_text": "stars"
            })
        slackBlocks.append({"type": "divider"})
        num = num + 1

    RichMessages =  {
        # "fulfillmentText": defaultPayload,
        "fulfillmentMessages": fulfillmentMessage,
        "payload": {
            "slack": {
                "attachments": [{
                    "blocks": slackBlocks
                }]
            },
        }
    }

    return RichMessages

