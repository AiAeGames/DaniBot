# AiAeBot
from api import generator, osu, ripple, tillerino, twitch, mysql, update
import json
import asyncio
import bottom
import requests
import pymysql
import re
from dispatcher import Dispatcher, connector, cooldown

with open("./config.json", "r") as f: 
    config = json.load(f)

connection = pymysql.connect(host=config['host'], user=config['user'], passwd=config['password'], db=config['database'])
connection.autocommit(True)
cursor = connection.cursor(pymysql.cursors.DictCursor)

ripple_bot = bottom.Client(host=config["ripple_irc"], port=6667, ssl=False)
twitch_bot = bottom.Client(host=config["twitch_irc"], port=6667, ssl=False)

async def autoupdate():
    await ripple_bot.wait("client_connect")
    await twitch_bot.wait("client_connect")
    while True:
        q_t = mysql.execute("SELECT * FROM ripple WHERE twitch_username IS NOT NULL AND twitch_username != ''")
        twitch_users = q_t.fetchall()
        for row in twitch_users:
            twitch_bot.send('JOIN', channel=("#" + row["twitch_username"]))
        res = mysql.execute("SELECT * FROM ripple")
        results = res.fetchall()
        for row in results:
            check_online = ripple.isonline(id=row["user_id"])
            if check_online["result"] == True:
                msg = update.user_update(username=row["username"], update=False)
                if msg != None:
                    if row["osu_bot"] == 1:
                        ripple_bot.send("privmsg", target=row["username"], message=msg)
                        if row["twitch_bot"] != 1:
                            update.user_update(username=row["username"], update=True)
                    if row["twitch_bot"] == 1:
                        twitch_bot.send("privmsg", target=("#" + row["twitch_username"]), message=msg)
                        update.user_update(username=row["username"], update=True)
        await asyncio.sleep(20, loop=ripple_bot.loop)

class TwitchBot(Dispatcher):
    def shutdown(self, nick, message, channel):
        if nick in config['owners']:
            self.respond(self, message="Sayonara", channel=channel, nick=nick)
            quit()

    @cooldown(10)
    def beatmap_request(self, nick, message, channel):
        res = mysql.execute("SELECT * FROM ripple WHERE twitch_username=%s", [channel.replace("#", "")])
        results = res.fetchone()
        if results["twitch_bot"] == 1:
            mods = re.findall("(HR|DT|NC|FL|HD|SD|PF|NF|EZ|HT)", message)
            o_id = re.search("\/[bsd]\/([0-9]+?)(?:\s|$|\?|&)", message).group(1)
            link = re.search("\/[bsd]\/", message).group(0)
            remove_lines = re.search("[bsd]", link).group(0)
            if remove_lines == "b":
                o = osu.get_beatmap(b=o_id, m=0)
                if o:
                    id = o[0]["beatmap_id"]
            elif remove_lines == "s":
                o = osu.get_beatmap(s=o_id, m=0)
                if o:
                    id = o[len(o)-1]["beatmap_id"]
            if o:
                t = tillerino.beatmapinfo(id, mods)
                all_mods = ''.join(mods)
                if t["oppaiOnly"] == True:
                    oppai = "Oppai"
                else:
                    oppai = ""
                artist = o[0]["artist"]
                title = o[0]["title"]
                creator = o[0]["creator"]
                version = o[0]["version"]
                bmset = o[0]["beatmapset_id"]
                bpm = o[0]["bpm"]
                star = int(t["starDiff"])
                if "DT" in mods or "NC" in mods:
                    bpm = int(float(bpm) * 1.5)
                elif "HT" in mods:
                    bpm = int(float(bpm) / 1.33)
                else:
                    bpm = bpm
                acc98 = int(t["ppForAcc"]["entry"][9]["value"])
                acc99 = int(t["ppForAcc"]["entry"][11]["value"])
                osulink = "https://osu.ppy.sh/{}/{}".format(remove_lines, o_id)
                bloodcatlink = "http://m.blosu.net/{}.osz".format(bmset)
                ripple_msg = "{} > [{} {} - {} [{}]] [{} Blosu] {} | {}BPM, {} ★ (98% {}pp | 99% {}pp)".format(nick.split(".", 1)[0], osulink, artist, title, version, bloodcatlink, all_mods, bpm, star, acc98, acc99)
                twitch_msg = "{} - {} [{}] {} | {}BPM, {} ★ (98% {}pp | 99% {}pp) {}".format(artist, title, version, all_mods, bpm, star, acc98, acc99, oppai)
                twitch_bot.send("privmsg", target=channel, message=twitch_msg)
                ripple_bot.send("privmsg", target=results["username"], message=ripple_msg)

    def command_patterns(self):
        return (
            ('!shutdown', self.shutdown),
            ('^http[s]?:\/\/osu\.ppy\.sh\/(b|s)\/[0-9]+', self.beatmap_request),
        )

class RippleBot(Dispatcher):

    def shutdown(self, nick, message, channel):
        if nick in config['owners']:
            self.respond(message="Sayonara", channel=channel, nick=nick)
            quit()

    @cooldown(60)
    def login(self, nick, message, channel):
        ripple_api = ripple.user(name=nick)
        if mysql.checker(user_id=ripple_api["id"]) == False:
            api = generator.key()
            url = "https://pi.aiaegames.xyz/login_api.php?k={}".format(api)
            text = "To login click [" + url + " here]. Thanks for using AiAeBot."
            mysql.execute("INSERT INTO ripple (user_id, username, api) VALUES(%s, %s, %s)", [ripple_api["id"], nick, api])
            self.respond(message=text, channel=channel, nick=nick)
        else:
            q = mysql.execute("SELECT * FROM ripple WHERE user_id=%s", [ripple_api["id"]])
            result = q.fetchone()
            url = "https://pi.aiaegames.xyz/login_api.php?k={}".format(result["api"])
            self.respond(message="Click this [" + url + " link] to login.", channel=channel, nick=nick)

    @cooldown(5)
    def mode(self, nick, message, channel):
        if mysql.checker(username=nick) == True:
            ripple_api = ripple.user(name=nick)
            mode = ''.join(re.findall('\d+', message))
            self.respond(message="Mode is set to {}.".format(mode), channel=channel, nick=nick)
            mysql.execute("UPDATE ripple SET mode=%s WHERE user_id=%s", [mode, ripple_api["id"]])
        else:
            self.respond(message="New username? Please go to settings and update it :).", channel=channel, nick=nick)

    @cooldown(60)
    def help(self, nick, message, channel):
        self.respond(message="Click [https://pi.aiaegames.xyz/commands.php here] to see commands.", channel=channel, nick=nick)

    def command_patterns(self):
        return (
            ('!mode [0-3]', self.mode),
            ('!login', self.login),
            ('!kys', self.shutdown),
            ('!help', self.help),
        )

ripple_dispatcher = RippleBot(ripple_bot)
twitch_dispatcher = TwitchBot(twitch_bot)
connector(ripple_bot, ripple_dispatcher, config["ripple_user"], ["#haitai", "#requests"], config["ripple_password"])
connector(twitch_bot, twitch_dispatcher, config["twitch_user"], "", config["twitch_password"])
try:
    ripple_bot.loop.create_task(autoupdate())
except KeyboardInterrupt as e:
    print("ImTriggered")

ripple_bot.loop.create_task(ripple_bot.connect())
ripple_bot.loop.create_task(twitch_bot.connect())
ripple_bot.loop.run_forever()