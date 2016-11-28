import requests
import re
import json
import pymysql

import ripple_api as ripple
import danibot_api as danibot

with open("./config.json", "r") as f: 
    config = json.load(f)

connection = pymysql.connect(host=config['db_host'], user=config['db_user'], passwd=config['db_pass'], db=config['db_table'])
connection.autocommit(True)
cursor = connection.cursor(pymysql.cursors.DictCursor)


def user_settings(username, twitch_username=None):
    make_array = {}
    if username != "":
        r = ripple.user(name=username)
        user_id = r["id"]
    else:
        user_id = "1"
    
    cursor.execute("SELECT * FROM ripple_tracking WHERE user_id=%s or twitch_username=%s", [user_id, twitch_username])
    row = cursor.fetchone()
    make_array["user_id"] = row["user_id"]
    make_array["mode"] = row["mode"]
    make_array["twitch_bot"] = row["twitch_bot"]
    make_array["osu_bot"] = row["osu_bot"]
    make_array["twitch_username"] = "#" + row["twitch_username"]
    return make_array

def find_user(username):
    r = ripple.user(name=username)
    cursor.execute("SELECT * FROM ripple_tracking WHERE user_id='%s'" , [r["id"]])
    counter = cursor.rowcount
    if counter == 1:
        return True
    else:
        return False

def find_ripple_user(channel):
    channel = channel.replace("#", "")
    cursor.execute("SELECT * FROM ripple_tracking WHERE twitch_username=%s", [channel])
    row = cursor.fetchone()
    return row["username"].replace(" ", "_")

def get_user_settings(username):
    make_array = {}
    r = ripple.user(name=username)
    cursor.execute("SELECT * FROM ripple_tracking WHERE user_id=%s", [r["id"]])
    row = cursor.fetchone()
    make_array["mode_id"] = row["mode"]
    if row["mode"] == 0:
        make_array["mode"] = "Standard"
    elif row["mode"] == 1:
        make_array["mode"] = "Taiko"
    elif row["mode"] == 2:
        make_array["mode"] = "CtB"
    else:
        make_array["mode"] = "Mania"
    if row["osu_bot"] == 1:
        make_array["osu_bot"] = "Enabled"
    else:
        make_array["osu_bot"] = "Disabled"
    if row["twitch_bot"] == 1:
        make_array["twitch_bot"] = "Enabled"
    else:
        make_array["twitch_bot"] = "Disabled"
    return make_array

def user_update(username):
    u_s = get_user_settings(username)
    r = ripple.user(name=username)
    cursor.execute("SELECT * FROM ripple_tracking WHERE user_id='%s'" , [r["id"]])
    row = cursor.fetchone()
    if u_s["mode_id"] == 0:
        if r["std"]["pp"] != row["std_pp"] and (r["std"]["pp"]-1) != row["std_pp"] and (r["std"]["pp"]+1) != row["std_pp"]:
            rank = r["std"]["global_leaderboard_rank"]
            pp = r["std"]["pp"]
            msg = "Rank %+d (%+d pp)" % ((row["std_rank"] - rank), (pp - row["std_pp"]))
            cursor.execute("UPDATE ripple_tracking SET std_pp=%s, std_rank=%s WHERE user_id=%s", [pp, rank, r["id"]])
            return msg
    elif u_s["mode_id"] == 1:
        if r["taiko"]["ranked_score"] != row["taiko_score"]:
            rank = r["taiko"]["global_leaderboard_rank"]
            pp = r["taiko"]["ranked_score"]
            msg = "Rank %+d (%+d score)" % ((row["taiko_rank"] - rank), (score - row["taiko_score"]))
            cursor.execute("UPDATE ripple_tracking SET taiko_score=%s, taiko_rank=%s WHERE user_id=%s", [score, rank, r["id"]])
            return msg
    elif u_s["mode_id"] == 2:
        if r["ctb"]["ranked_score"] != row["ctb_score"]:
            rank = r["ctb"]["global_leaderboard_rank"]
            pp = r["ctb"]["ranked_score"]
            msg = "Rank %+d (%+d score)" % ((row["ctb_rank"] - rank), (score - row["ctb_score"]))
            cursor.execute("UPDATE ripple_tracking SET ctb_score=%s, ctb_rank=%s WHERE user_id=%s", [score, rank, r["id"]])
            return msg
    elif u_s["mode_id"] == 3:
        if r["mania"]["pp"] != row["mania_pp"]:
            rank = r["mania"]["global_leaderboard_rank"]
            pp = r["mania"]["pp"]
            msg = "Rank %+d (%+d pp)" % ((row["mania_rank"] - rank), (pp - row["mania_pp"]))
            cursor.execute("UPDATE ripple_tracking SET mania_pp=%s, mania_rank=%s WHERE user_id=%s", [pp, rank, r["id"]])
            return msg

def mode_update(mode, username):
    r = ripple.user(name=username)
    cursor.execute("UPDATE ripple_tracking SET mode=%s WHERE user_id=%s", [mode, r["id"]])
    connection.commit()

def bot_update(option, username):
    r = ripple.user(name=username)
    cursor.execute("SELECT * FROM ripple_tracking WHERE user_id=%s", [r["id"]])
    row = cursor.fetchone()
    if option == "ingame":
        if row["osu_bot"] == 0:
            cursor.execute("UPDATE ripple_tracking SET osu_bot=1 WHERE user_id=%s", [r["id"]])
            connection.commit()
        else:
            cursor.execute("UPDATE ripple_tracking SET osu_bot=0 WHERE user_id=%s", [r["id"]])
            connection.commit()
    else:
        if row["twitch_bot"] == 0:
            cursor.execute("UPDATE ripple_tracking SET twitch_bot=1 WHERE user_id=%s", [r["id"]])
            connection.commit()
        else:
            cursor.execute("UPDATE ripple_tracking SET twitch_bot=0 WHERE user_id=%s", [r["id"]])
            connection.commit()

def bot_last(channel):
    d = danibot.user_settings("", channel.replace("#", ""))
    r = ripple.recent(id=d["user_id"], mode=d["mode"])
    song_name = r["scores"][0]["beatmap"]["song_name"]
    acc = r["scores"][0]["accuracy"]
    if d["mode"] == 0:
        stars = r["scores"][0]["beatmap"]["difficulty"]
        pp = r["scores"][0]["pp"]
        return "{} ({:.2f}%) {:.2f}pp | {:.2f}".format(song_name, acc, pp, stars)
    elif d["mode"] == 1:
        score = "{:,} score".format(r["scores"][0]["score"])
        return "{} - {}".format(song_name, score)
    elif d["mode"] == 2:
        score = "{:,} score".format(r["scores"][0]["score"])
        return "{} - {}".format(song_name, score)
    elif d["mode"] == 3:
        pp = r["scores"][0]["pp"]
        stars = r["scores"][0]["beatmap"]["difficulty2"]["mania"]
        count = "{} MAX / {} / {} / {} / {}".format(r["scores"][0]["count_geki"],r["scores"][0]["count_300"], (r["scores"][0]["count_100"] + r["scores"][0]["count_katu"]), r["scores"][0]["count_50"], r["scores"][0]["count_miss"])
        if r["scores"][0]["full_combo"] == True:
            fc = "FC"
        else:
            fc = "NoFC"
        return "{} <Mania> | {:.2f} \u2605 | {:.2f}pp | {} | {} | {:.2f}%".format(song_name, stars, pp, count, fc, acc)