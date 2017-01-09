# blosu

import requests
import re
import json

with open("/home/aiae/r/config.json", "r") as f: 
    config = json.load(f)

def get_beatmapset(q=None, p=0):
    try:
        request = requests.get("http://m.blosu.net/api/", params={"q" : q, "p" : p})
    except requests.exceptions.RequestException as e:
        return
    return json.loads(request.text)