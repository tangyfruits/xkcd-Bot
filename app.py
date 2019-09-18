import os
import sys
import json
import urllib2
import requests
import random
from bs4 import BeautifulSoup
from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "This page acts as a Webhook for the xkcd Bot on Facebook", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging even
    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message
                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text
                    send_message_xkcd(sender_id, message_text)

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200

def send_message_xkcd(recipient_id, message_text):

    #need to get xkcd cd json links
    url_head = "http://xkcd.com/"
    url_tail = "/info.0.json"
    #random_int = str(random.randint(1,get_xkcd_latest()))
    response = urllib2.urlopen(url_head + get_xkcd_latest() + url_tail)
    xkcd_data = json.load(response)
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
         "message":{
            "attachment":{
                "type":"image",
                    "payload":{
                        "url":xkcd_data["img"],
                                }
                        },
                        "quick_replies":[
      {
        "content_type":"text",
        "title":"Previous",
        "payload":"DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_PREVIOUS"
      },
       {
         "content_type":"text",
         "title":"Next",
         "payload":"DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_NEXT"
       },
      {
        "content_type":"text",
        "title":"Random",
        "payload":"DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_RANDOM"
      }
    ]
                    }
    })
    r = requests.post("https://graph.facebook.com/v2.9/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        
def get_xkcd_latest():
    soup = BeautifulSoup(requests.get('http://www.xkcd.com').text, 'html.parser')
    xkcdid = soup.find("meta",  property="og:url")
    return str(xkcdid).split("/")[3]
 
        
def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
