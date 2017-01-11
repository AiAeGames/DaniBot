# osu!api
# https://github.com/ppy/osu-api/wiki

import requests
import re
import json

with open("/home/aiae/r/config.json", "r") as f: 
    config = json.load(f)

def get_beatmap(b=None, s=None, m=0):
    try:
        if b != None:
            request = requests.get("https://osu.ppy.sh/api/get_beatmaps", params={"k" : config["osu_token"], "b" : b, "m" : m})
        else:
            request = requests.get("https://osu.ppy.sh/api/get_beatmaps", params={"k" : config["osu_token"], "s" : s, "m" : m})
    except requests.exceptions.RequestException as e:
        return
    return json.loads(request.text)