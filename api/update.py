from api import generator, osu, ripple, tillerino, twitch, mysql
import json
import asyncio
import bottom
import requests
import pymysql
import re

def user_update(username, update=False):
    r =  ripple.user(id=username)
    cursor = mysql.execute("SELECT * FROM ripple WHERE user_id='%s'" , [r["id"]])
    row = cursor.fetchone()
    if row["mode"] == 0:
        if r["std"]["pp"] != row["std_pp"]:
            rank = r["std"]["global_leaderboard_rank"]
            pp = r["std"]["pp"]
            msg = "Rank %+d (%+d pp)" % ((row["std_rank"] - rank), (pp - row["std_pp"]))
            if update == True:
                mysql.execute("UPDATE ripple SET std_pp=%s, std_rank=%s WHERE user_id=%s", [pp, rank, r["id"]])
            return msg
    elif row["mode"] == 1:
        if r["taiko"]["ranked_score"] != row["taiko_score"]:
            rank = r["taiko"]["global_leaderboard_rank"]
            score = r["taiko"]["ranked_score"]
            msg = "Rank %+d (%+d score)" % ((row["taiko_rank"] - rank), (score - row["taiko_score"]))
            if update == True:
                mysql.execute("UPDATE ripple SET taiko_score=%s, taiko_rank=%s WHERE user_id=%s", [score, rank, r["id"]])
            return msg
    elif row["mode"] == 2:
        if r["ctb"]["ranked_score"] != row["ctb_score"]:
            rank = r["ctb"]["global_leaderboard_rank"]
            score = r["ctb"]["ranked_score"]
            msg = "Rank %+d (%+d score)" % ((row["ctb_rank"] - rank), (score - row["ctb_score"]))
            if update == True:
                mysql.execute("UPDATE ripple SET ctb_score=%s, ctb_rank=%s WHERE user_id=%s", [score, rank, r["id"]])
            return msg
    elif row["mode"] == 3:
        if r["mania"]["pp"] != row["mania_pp"]:
            rank = r["mania"]["global_leaderboard_rank"]
            pp = r["mania"]["pp"]
            msg = "Rank %+d (%+d pp)" % ((row["mania_rank"] - rank), (pp - row["mania_pp"]))
            if update == True:
                mysql.execute("UPDATE ripple SET mania_pp=%s, mania_rank=%s WHERE user_id=%s", [pp, rank, r["id"]])
            return msg