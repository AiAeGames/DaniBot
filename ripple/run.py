from irc import IRCBot, IRCConnection
import json
import MySQLdb
import requests
import re
try:
    with open("./config.json", "r") as f: 
        get = json.load(f)
except:
    print("Config file is not found!")
    raise
    sys.exit()

db = MySQLdb.connect(host=get['host'], user=get['user'], passwd=get['passwd'], db=get['db']) 
cursor  = db.cursor()

def run_bot(bot_class, host, port, nick, password=None, channels=None, ssl=None):
    conn = IRCConnection(host, port, nick, password=password, needs_registration=False)
    bot_instance = bot_class(conn)

    channels = channels or []
    conn.connect()
    for channel in channels:
        conn.join(channel)

    conn.enter_event_loop()


class Bot(IRCBot):
    
    def shutdown(self, nick, message, channel):
        if nick == get["bot_owner"]: 
            self.respond("Bot is shutting down.", nick=nick)
            quit()

    def help(self, nick, message, channel):
        self.respond("Click [http://google.bg here] for %s's full command list." % get["irc_nick"], nick=nick)

    def trackme(self, nick, message, channel):
        pjson = requests.get("http://ripple.moe/api/v1/users/full?name={}".format(nick))
        data = json.loads(pjson.text)
        cursor.execute("SELECT * FROM ripple_tracking WHERE user_id='%s'" , [data["id"]])
        counter = cursor.rowcount
        if counter == 1:
            self.respond("I am stalking you already...", nick=nick)
        else:
            cursor.execute("INSERT INTO ripple_tracking (user_id, username, mode, std_rank, std_pp, taiko_rank, taiko_score, ctb_rank, ctb_score, mania_rank, mania_pp) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" , [data["id"], data["username"], 0, data["std"]["global_leaderboard_rank"], data["std"]["pp"], data["taiko"]["global_leaderboard_rank"], data["taiko"]["ranked_score"], data["ctb"]["global_leaderboard_rank"], data["ctb"]["ranked_score"], data["mania"]["global_leaderboard_rank"], data["mania"]["pp"]])
            db.commit()
            self.respond("%s is now tracking all your modes." % get["irc_nick"], nick=nick)

    def std():
        return 

    def update(self, nick, message, channel):
        pjson = requests.get("http://ripple.moe/api/v1/users/full?name={}".format(nick))
        data = json.loads(pjson.text)
        cursor.execute("SELECT mode FROM ripple_tracking WHERE user_id='%s'" , [data["id"]])
        row = cursor.fetchone()
        counter = cursor.rowcount
        if counter == 1:
            if row[0] == 0:
                self.respond("You are trying to update your std pp.", nick=nick)
            if row[0] == 1:
                self.respond("You are trying to update your taiko score.", nick=nick)
            if row[0] == 2:
                self.respond("You are trying to update your CtB score.", nick=nick)
            if row[0] == 3:
                self.respond("You are trying to update your mania pp.", nick=nick)
        else:
            self.respond("You are not in my stalk list. You can signup with !stalkme.", nick=nick)

    def mode(self, nick, message, channel):
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
                cursor.execute("UPDATE ripple_tracking SET mode='%s' WHERE user_id='%d'" , [mode, data["id"]])
                db.commit()
            else:
                self.respond("Mode not found. Numbers are supported only for now.", nick=nick)

    def command_patterns(self):
        return (
            ('-shutdown', self.shutdown),
            ('!help', self.help),
            ('!stalkme', self.trackme),
            ('!update', self.update),
            ('!u$', self.update),
            ('!mode', self.mode),
        )

run_bot(Bot, get["irc_host"], 6667, get["irc_nick"], get["irc_password"], channels=get["channels"])
