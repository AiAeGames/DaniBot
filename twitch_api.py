# twitch!api

import requests
import json

with open("./config.json", "r") as f: 
    config = json.load(f)

def twitch_online(twitch_name):
    try:
        twitchJson = requests.get("https://api.twitch.tv/kraken/streams/{}".format(twitch_name), headers={'Client-ID': config["twitch_token"]})
    except requests.exceptions.RequestException as e:
        return
    data = json.loads(twitchJson.text)
    if data['stream'] == None:
        return False
    else:
        return True