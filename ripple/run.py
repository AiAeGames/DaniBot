import asyncio
import bottom
import json
import pymysql
import requests
import re
from dispatcher import Dispatcher, connector, cooldown

try:
    with open("./config.json", "r") as f: 
        get = json.load(f)
except:
    print("Config file is not found!")
    raise
    sys.exit()

bot = bottom.Client(host=get["irc_host"], port=6667, ssl=False)
connection = pymysql.connect(host=get['host'], user=get['user'], passwd=get['passwd'], db=get['db']) 
connection.autocommit(True)
cursor = connection.cursor(pymysql.cursors.DictCursor)

def isOnline(user_id):
    try:
        onlineJson = requests.get("http://c.ripple.moe/api/v1/isOnline?id={}".format(user_id), headers={'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5'})
    except requests.exceptions.RequestException as e:
        return
    data = json.loads(onlineJson.text)
    if(data["result"] == True):
        return True
    else:
        return False

def u_std(user_id, nick, pp, rank):
    cursor.execute("SELECT * FROM ripple_tracking WHERE user_id='%s'" , [user_id])
    row = cursor.fetchone()
    if pp == row["std_pp"]:
        return False
    else:
        bot.send("privmsg", target=nick, message="Rank %+d (%+d pp)" % ((row["std_rank"] - rank), (pp - row["std_pp"])))
        cursor.execute("UPDATE ripple_tracking SET std_pp=%s, std_rank=%s WHERE user_id=%s", [pp, rank, user_id])

def u_taiko(user_id, nick, score, rank): 
    cursor.execute("SELECT * FROM ripple_tracking WHERE user_id='%s'" , [user_id])
    row = cursor.fetchone()
    if score == row["taiko_score"]:
        return False
    else:
        bot.send("privmsg", target=nick, message="Rank %+d (%+d score)" % ((row["taiko_rank"] - rank), (score - row["taiko_score"])))
        cursor.execute("UPDATE ripple_tracking SET taiko_score=%s, taiko_rank=%s WHERE user_id=%s", [score, rank, user_id])

def u_ctb(user_id, nick, score, rank):   
    cursor.execute("SELECT * FROM ripple_tracking WHERE user_id='%s'" , [user_id])
    row = cursor.fetchone()
    if score == row["ctb_score"]:
        return False
    else:
        bot.send("privmsg", target=nick, message="Rank %+d (%+d score)" % ((row["ctb_rank"] - rank), (score - row["ctb_score"])))
        cursor.execute("UPDATE ripple_tracking SET ctb_score=%s, ctb_rank=%s WHERE user_id=%s", [score, rank, user_id])

def u_mania(user_id, nick, pp, rank):    
    cursor.execute("SELECT * FROM ripple_tracking WHERE user_id='%s'" , [user_id])
    row = cursor.fetchone()
    if pp == row["mania_pp"]:
        return False
    else:
        bot.send("privmsg", target=nick, message="Rank %+d (%+d pp)" % ((row["mania_rank"] - rank), (pp - row["mania_pp"])))
        cursor.execute("UPDATE ripple_tracking SET mania_pp=%s, mania_rank=%s WHERE user_id=%s", [pp, rank, user_id])

async def autoupdate():
    await bot.wait("client_connect")
    while not bot.protocol.closed:
        cursor.execute("SELECT * FROM ripple_tracking WHERE stalk=1",)
        counter = cursor.rowcount
        if counter > 0:
            cursor.execute("SELECT * FROM ripple_tracking WHERE stalk=1")
            results = cursor.fetchall()
            for row in results:
                if(isOnline(row["user_id"]) == True):
                    try:
                        pjson = requests.get("http://ripple.moe/api/v1/users/full?name={}".format(row["username"]), headers={'token': get["token"]})
                    except requests.exceptions.RequestException as e:
                        return
                    data = json.loads(pjson.text)
                    username = row["username"].replace(" ", "_")
                    if row["mode"] == 0:
                        u_std(data["id"], username, data["std"]["pp"], data["std"]["global_leaderboard_rank"])
                    if row["mode"] == 1:
                        u_taiko(data["id"], username, data["taiko"]["ranked_score"], data["taiko"]["global_leaderboard_rank"])
                    if row["mode"] == 2:
                        u_ctb(data["id"], username, data["ctb"]["ranked_score"], data["ctb"]["global_leaderboard_rank"])
                    if row["mode"] == 3:
                        u_mania(data["id"], username, data["mania"]["pp"], data["mania"]["global_leaderboard_rank"])
                else:
                    cursor.execute("UPDATE ripple_tracking SET stalk=0 WHERE user_id=%s", [row["user_id"]])
        await asyncio.sleep(30, loop=bot.loop)

class IrcBot(Dispatcher):
    def shutdown(self, nick, message, channel):
        if nick == get["bot_owner"]: 
            self.respond("Bot is shutting down.", nick=nick)
            quit()
    
    @cooldown(60)
    def h(self, nick, message, channel):
        self.respond("DaniBot is in Beta, if you find any bugs or bot is slow you can find in userpage how to contact me.", nick=nick)
        self.respond("To turn on DaniBot: ", nick=nick)
        self.respond("1. Write !stalkme", nick=nick)
        self.respond("2. To change mode use !m from 0 to 3", nick=nick)
        self.respond("3. To manually update pp write !u", nick=nick)
        self.respond("4. To turn on auto update write !stalk if you want to turn if off write it again.", nick=nick)
    
    @cooldown(10)
    def trackme(self, nick, message, channel):
        pjson = requests.get("http://ripple.moe/api/v1/users/full?name={}".format(nick))
        data = json.loads(pjson.text)
        cursor.execute("SELECT * FROM ripple_tracking WHERE user_id=%s", [data["id"]])
        counter = cursor.rowcount
        if counter == 1:
            self.respond("I'm already stalking you...", nick=nick)
        else:
            cursor.execute("INSERT INTO ripple_tracking (user_id, username, std_rank, std_pp, taiko_rank, taiko_score, ctb_rank, ctb_score, mania_rank, mania_pp) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" , [data["id"], data["username"], data["std"]["global_leaderboard_rank"], data["std"]["pp"], data["taiko"]["global_leaderboard_rank"], data["taiko"]["ranked_score"], data["ctb"]["global_leaderboard_rank"], data["ctb"]["ranked_score"], data["mania"]["global_leaderboard_rank"], data["mania"]["pp"]])
            connection.commit()
            cursor.execute("INSERT INTO ripple_tracking_twitch (user_id, username, std_rank, std_pp, taiko_rank, taiko_score, ctb_rank, ctb_score, mania_rank, mania_pp) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" , [data["id"], data["username"], data["std"]["global_leaderboard_rank"], data["std"]["pp"], data["taiko"]["global_leaderboard_rank"], data["taiko"]["ranked_score"], data["ctb"]["global_leaderboard_rank"], data["ctb"]["ranked_score"], data["mania"]["global_leaderboard_rank"], data["mania"]["pp"]])
            connection.commit()
            self.respond("%s is now tracking all your modes." % get["irc_nick"], nick=nick)
    
    @cooldown(10)
    def u(self, nick, message, channel):
        pjson = requests.get("http://ripple.moe/api/v1/users/full?name={}".format(nick))
        data = json.loads(pjson.text)
        cursor.execute("SELECT * FROM ripple_tracking WHERE user_id='%s'" , [data["id"]])
        row = cursor.fetchone()
        counter = cursor.rowcount
        if counter == 1:
            if row["mode"] == 0:
                u_std(data["id"], nick, data["std"]["pp"], data["std"]["global_leaderboard_rank"])
            if row["mode"] == 1:
                u_taiko(data["id"], nick, data["taiko"]["ranked_score"], data["taiko"]["global_leaderboard_rank"])
            if row["mode"] == 2:
                u_ctb(data["id"], nick, data["ctb"]["ranked_score"], data["ctb"]["global_leaderboard_rank"])
            if row["mode"] == 3:
                u_mania(data["id"], nick, data["mania"]["pp"], data["mania"]["global_leaderboard_rank"])
        else:
            return False
    
    @cooldown(10)
    def m(self, nick, message, channel):
        pjson = requests.get("http://ripple.moe/api/v1/users/full?name={}".format(nick))
        data = json.loads(pjson.text)
        cursor.execute("SELECT * FROM ripple_tracking WHERE user_id='%s'" , [data["id"]])
        counter = cursor.rowcount
        if counter == 1:
            mode = re.findall('\d+', message)
            mode = ''.join(mode)
            if "0" <= mode <= "3":
                if mode == "0": 
                    mode_s = "Standard"
                if mode == "1":
                    mode_s = "Taiko"
                if mode == "2":
                    mode_s = "Catch the Beat"
                if mode == "3":
                    mode_s = "Mania"
                self.respond("Mode is set to {}.".format(mode_s), nick=nick)
                cursor.execute("UPDATE ripple_tracking SET mode=%s WHERE user_id=%s", [mode, data["id"]])
                connection.commit()
                cursor.execute("UPDATE ripple_tracking_twitch SET mode=%s WHERE user_id=%s", [mode, data["id"]])
                connection.commit()
            else:
                return False
        else:
            return False

    @cooldown(10)
    def stalk(self, nick, message, channel):
        pjson = requests.get("http://ripple.moe/api/v1/users/full?name={}".format(nick))
        data = json.loads(pjson.text)
        cursor.execute("SELECT * FROM ripple_tracking WHERE user_id='%s'" , [data["id"]])
        row = cursor.fetchone()
        counter = cursor.rowcount
        if counter == 1:
            if row["stalk"] == 1:
                self.respond("Stalking is off.", nick=nick)
                cursor.execute("UPDATE ripple_tracking SET stalk=0 WHERE user_id=%s", [data["id"]])
                connection.commit()
                cursor.execute("UPDATE ripple_tracking_twitch SET stalk=0 WHERE user_id=%s", [data["id"]])
                connection.commit()
            else:
                self.respond("Stalking is on, when you go offline stalk will turn off automatically.", nick=nick)
                cursor.execute("UPDATE ripple_tracking SET stalk=1 WHERE user_id=%s", [data["id"]])
                connection.commit()
                cursor.execute("UPDATE ripple_tracking_twitch SET stalk=1 WHERE user_id=%s", [data["id"]])
                connection.commit()
        else:
            return False

    @cooldown(10)
    def l(self, nick, message, channel):
        u_json = requests.get("http://ripple.moe/api/v1/users/full?name={}".format(nick))
        u_data = json.loads(u_json.text)
        cursor.execute("SELECT mode FROM ripple_tracking WHERE user_id='%s'" , [u_data["id"]])
        row = cursor.fetchone()
        l_json = requests.get("https://ripple.moe/api/v1/users/scores/recent?id={}&mode={}&l=1".format(u_data["id"], row["mode"]))
        l_data = json.loads(l_json.text)
        if row["mode"] == 0:
            pp_or_score = "{:,} pp".format(l_data["scores"][0]["pp"])
            self.respond("{} - {}".format(l_data["scores"][0]["beatmap"]["song_name"], pp_or_score), nick=nick)
        elif row["mode"] == 3:
            #Yuyoyuppe - AiAe NM | 2,8 ☆ | 40pp/120pp M | 300/80/-/-/- | FC/NoFC | acc%
            song_name = l_data["scores"][0]["beatmap"]["song_name"]
            stars = l_data["scores"][0]["beatmap"]["difficulty2"]["mania"]
            pp = l_data["scores"][0]["pp"]
            count = "{} MAX / {} / {} / {} / {}".format(l_data["scores"][0]["count_geki"],l_data["scores"][0]["count_300"], (l_data["scores"][0]["count_100"] + l_data["scores"][0]["count_katu"]), l_data["scores"][0]["count_50"], l_data["scores"][0]["count_miss"])
            if l_data["scores"][0]["full_combo"] == True:
                fc = "FC"
            else:
                fc = "NoFC"
            acc = l_data["scores"][0]["accuracy"]
            info = "{} <Mania> | {:.2f} \u2605 | {:.2f}pp | {} | {} | {:.2f}%".format(song_name, stars, pp, count, fc, acc)
            self.respond(info, nick=nick)
        else:
            pp_or_score = "{:,} score".format(l_data["scores"][0]["score"])
            self.respond("{} - {}".format(l_data["scores"][0]["beatmap"]["song_name"], pp_or_score), nick=nick)

    @cooldown(10)
    def t(self, nick, message, channel):
        self.respond(message="If you want my bot in your twitch channel DM me in discord AiAe*Games#2735.", nick=nick)
        
    def command_patterns(self):
        return (
            ('-shutdown', self.shutdown),
            ('!h', self.h),
            ('!stalkme', self.trackme),
            ('!u', self.u),
            ('!m', self.m),
            ('!t', self.m),
            ('!l', self.l),
            ('!stalk$', self.stalk),
        )

dispatcher = IrcBot(bot)
connector(bot, dispatcher, get["irc_nick"], "#bulgarian", get["irc_password"])
bot.loop.create_task(autoupdate())
bot.loop.create_task(bot.connect())
bot.loop.run_forever()
