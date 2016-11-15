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
    # TODO add is user online if not change stalk to false.
    await bot.wait("client_connect")
    while not bot.protocol.closed:
        cursor.execute("SELECT * FROM ripple_tracking WHERE stalk=1",)
        counter = cursor.rowcount
        if counter > 0:
            cursor.execute("SELECT * FROM ripple_tracking WHERE stalk=1")
            results = cursor.fetchall()
            for row in results:
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
        await asyncio.sleep(30, loop=bot.loop)

class IrcBot(Dispatcher):
    def shutdown(self, nick, message, channel):
        if nick == get["bot_owner"]: 
            self.respond("Bot is shutting down.", nick=nick)
            quit()
    
    @cooldown(60)
    def h(self, nick, message, channel):
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
                self.respond("Chaning mode to {}".format(mode_s), nick=nick)
                cursor.execute("UPDATE ripple_tracking SET mode=%s WHERE user_id=%s", [mode, data["id"]])
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
            else:
                self.respond("Stalking is on.", nick=nick)
                cursor.execute("UPDATE ripple_tracking SET stalk=1 WHERE user_id=%s", [data["id"]])
                connection.commit()
        else:
            return False

    def command_patterns(self):
        return (
            ('-shutdown', self.shutdown),
            ('!h', self.h),
            ('!stalkme', self.trackme),
            ('!u', self.u),
            ('!m', self.m),
            ('!stalk$', self.stalk),
        )

dispatcher = IrcBot(bot)
connector(bot, dispatcher, get["irc_nick"], "#bulgarian", get["irc_password"])
bot.loop.create_task(autoupdate())
bot.loop.create_task(bot.connect())
bot.loop.run_forever()
