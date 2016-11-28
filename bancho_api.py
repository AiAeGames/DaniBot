# osu!api
# https://github.com/ppy/osu-api/wiki

import requests
import re
import json

with open("./config.json", "r") as f: 
    config = json.load(f)

def get_beatmap(b=None, m=0):
    try:
        request = requests.get("https://osu.ppy.sh/api/get_beatmaps?k={}&b={}&m={}", params={"k" : config["osu_api"], "b" : b, "m" : m})
    except requests.exceptions.RequestException as e:
        return
    return json.loads(request.text)

def get_user(u, m=0, type=None, event_days=None):
    return ""

def get_scores(b, u, m=0, mods=None, type=None, limit=1):
    return ""

def get_user_best(u, m=0, limit=None, type=None):
    return ""

def get_user_recent(u, m=0, limit=None, type=None):
    return ""