import urllib.parse as urllib

def displayResults_slack2(results, public_url, header_msg, default_header_msg = None):
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

    if (default_header_msg == None): default_header_msg = header_msg
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
        subTitle = "Address:\t %s. \nPhone:\t %s. \nPrice Range:\t %s. \nCategory:\t %s. \nClosed:\t %s" % (r["address"], r["phone"], r["price_range"], r["category"], r["is_closed"])
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
        if (r["is_closed"] != ""): slackText1 = slackText1 + "%s\n" % (r["is_closed"])

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

