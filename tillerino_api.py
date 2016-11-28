#tillerino!api

import requests
import re
import json

with open("./config.json", "r") as f: 
    config = json.load(f)

def Mods(modsList):
    modsEnum = 0
    for i in modsList:
        if i == "NO":
            modsEnum = 0
            break
        elif i == "NF":
            modsEnum += 1
        elif i == "EZ":
            modsEnum += 2
        elif i == "HD":
            modsEnum += 8
        elif i == "HR":
            modsEnum += 16
        elif i == "DT":
            modsEnum += 64
        elif i == "HT":
            modsEnum += 256
        elif i == "NC":
            modsEnum += 512
        elif i == "FL":
            modsEnum += 1024
        else:
            modsEnum = 0
    return modsEnum

def beatmapinfo(beatmapid, mods=None):
    try:
        request = requests.get("https://api.tillerino.org/beatmapinfo", params={"k": config["tillerino_api"], "beatmapid": beatmapid, "mods": Mods(mods)})
        return json.loads(request.text)
    except requests.exceptions.RequestException as e:
        return
    else:
        return