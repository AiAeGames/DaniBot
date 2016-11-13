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
cursor = connection.cursor(pymysql.cursors.DictCursor)

async def autoupdate_or_some_shit():
    await bot.wait("client_connect")
    while not bot.protocol.closed:
        await asyncio.sleep(3, loop=bot.loop)

class IrcBot(Dispatcher):
    def shutdown(self, nick, message, channel):
        if nick == get["bot_owner"]: 
            self.respond("Bot is shutting down.", nick=nick)
            quit()
    
    @cooldown(10)
    def h(self, nick, message, channel):
        self.respond("Click [http://google.bg here] for %s's full command list." % get["irc_nick"], nick=nick)
    
    @cooldown(10)
    def trackme(self, nick, message, channel):
        pjson = requests.get("http://ripple.moe/api/v1/users/full?name={}".format(nick))
        data = json.loads(pjson.text)
        cursor.execute("SELECT * FROM ripple_tracking WHERE user_id=%s", [data["id"]])
        counter = cursor.rowcount
        if counter == 1:
            self.respond("I am stalking you already...", nick=nick)
        else:
            cursor.execute("INSERT INTO ripple_tracking (user_id, username, std_rank, std_pp, taiko_rank, taiko_score, ctb_rank, ctb_score, mania_rank, mania_pp) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" , [data["id"], data["username"], data["std"]["global_leaderboard_rank"], data["std"]["pp"], data["taiko"]["global_leaderboard_rank"], data["taiko"]["ranked_score"], data["ctb"]["global_leaderboard_rank"], data["ctb"]["ranked_score"], data["mania"]["global_leaderboard_rank"], data["mania"]["pp"]])
            connection.commit()
            self.respond("%s is now tracking all your modes." % get["irc_nick"], nick=nick)
    
    @cooldown(10)
    def u(self, nick, message, channel):

        def u_std(user_id, pp, rank):
            cursor.execute("SELECT * FROM ripple_tracking WHERE user_id='%s'" , [user_id])
            row = cursor.fetchone()
            if pp == row["std_pp"]:
                return "There is no pp change."
            else:
                return "Rank {} (+{}pp)".format((row["std_rank"]-rank), (pp-row["std_pp"]))
 
        def u_taiko(user_id, score, rank): 
            return "{} {} {} {}".format(user_id, score, rank)
 
        def u_ctb(user_id, score, rank):   
            return "{} {} {} {}".format(user_id, score, rank)

        def u_mania(user_id, pp, rank):    
            return "{} {} {} {}".format(user_id, pp, rank)
        
        pjson = requests.get("http://ripple.moe/api/v1/users/full?name={}".format(nick))
        data = json.loads(pjson.text)
        cursor.execute("SELECT * FROM ripple_tracking WHERE user_id='%s'" , [data["id"]])
        row = cursor.fetchone()
        counter = cursor.rowcount
        if counter == 1:
            if row["mode"] == 0:
                self.respond(u_std(data["id"], data["std"]["pp"], data["std"]["global_leaderboard_rank"]), nick=nick)
            if row["mode"] == 1:
                self.respond(u_taiko(data["id"], data["taiko"]["ranked_score"], data["taiko"]["global_leaderboard_rank"]), nick=nick)
            if row["mode"] == 2:
                self.respond(u_ctb(data["id"], data["ctb"]["ranked_score"], data["ctb"]["global_leaderboard_rank"]), nick=nick)
            if row["mode"] == 3:
                self.respond(u_mania(data["id"], data["mania"]["pp"], data["mania"]["global_leaderboard_rank"]), nick=nick)
        else:
            self.respond("You are not in my stalk list. You can signup with !stalkme.", nick=nick)
    
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
                self.respond("Mode not found. Numbers are supported only for now.", nick=nick)
        else:
            self.respond("You are not in my stalk list. You can signup with !stalkme.", nick=nick)

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
            self.respond("You are not in my stalk list. You can signup with !stalkme.", nick=nick)

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
bot.loop.create_task(autoupdate_or_some_shit())
bot.loop.create_task(bot.connect())
bot.loop.run_forever()
