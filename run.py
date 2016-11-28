import bancho_api as bancho
import ripple_api as ripple
import tillerino_api as tillerino
import twitch_api as twitch
import danibot_api as danibot

import json
import asyncio
import bottom
import requests
import pymysql
import re
from dispatcher import Dispatcher, connector, cooldown

with open("./config.json", "r") as f: 
    config = json.load(f)

connection = pymysql.connect(host=config['db_host'], user=config['db_user'], passwd=config['db_pass'], db=config['db_table'])
connection.autocommit(True)
cursor = connection.cursor(pymysql.cursors.DictCursor)

ripple_bot = bottom.Client(host=config["ripple_server"], port=6667, ssl=False)
twitch_bot = bottom.Client(host=config["twitch_server"], port=6667, ssl=False)

async def autoupdate():
    await ripple_bot.wait("client_connect")
    while not ripple_bot.protocol.closed:
        cursor.execute("SELECT * FROM ripple_tracking WHERE osu_bot=1")
        results = cursor.fetchall()
        for row in results:
            on = ripple.isonline(name=row["username"])
            if on["result"] == True:
                msg = danibot.user_update(row["username"])
                if msg != None:
                    if row["osu_bot"] == 1:
                        ripple_bot.send("privmsg", message=msg, target=(row["username"].replace(" ", "_")))
                    if row["twitch_username"] != "" and row["twitch_bot"] == 1:
                        twitch_bot.send("privmsg", message=msg, target=("#" + row["twitch_username"]))
        await asyncio.sleep(30, loop=ripple_bot.loop)

class TwitchBot(Dispatcher):
    def shutdown(self, nick, message, channel):
        if nick == config["twitch_owner"]:
            quit()
    
    @cooldown(10)
    def beatmap_request(self, nick, message, channel):
        u_s = danibot.user_settings(danibot.find_ripple_user(channel))
        if u_s["twitch_bot"] == 1:
            mods = re.findall("(HR|DT|NC|FL|HD|SD|PF|NF|EZ|HT)", message)
            beatmap_id = re.search("\/[bsd]\/([0-9]+?)(?:\s|$|\?|&)", message).group(1)
            t = tillerino.beatmapinfo(beatmap_id, mods)
            b = bancho.get_beatmap(beatmap_id)
            d = danibot.find_ripple_user(channel)
            all_mods = ''.join(mods)
            artist = b[0]["artist"]
            title = b[0]["title"]
            creator = b[0]["creator"]
            version = b[0]["version"]
            bmset = b[0]["beatmapset_id"]
            bpm = b[0]["bpm"]
            #if "DT" in mods or "NC" in mods:
            #    bpm = int(float(bpm) * 1.5)
            #if "HT" in mods:
            #    bpm = int(float(bpm) / 1.33)
            acc98 = int(t["ppForAcc"]["entry"][9]["value"])
            acc99 = int(t["ppForAcc"]["entry"][11]["value"])
            osulink = "https://osu.ppy.sh/b/{}".format(beatmap_id)
            bloodcatlink = "http://bloodcat.com/osu/s/{}".format(bmset)
            twitch_bot.send("privmsg", target=channel, message="{} - {} [{}] {} | {}BPM, (98% {}pp | 99% {}pp)".format(artist, title, version, all_mods, bpm, acc98, acc99))
            ripple_bot.send("privmsg", target=d, message="{} > [{} {} - {} [{}]] [{} Bloodcat] {} | {}BPM, (98% {}pp | 99% {}pp)".format(nick.split(".", 1)[0], osulink, artist, title, version, bloodcatlink, all_mods, bpm, acc98, acc99))
                     
    @cooldown(30)
    def last(self, nick, message, channel): 
        twitch_bot.send("privmsg", target=channel, message=danibot.bot_last(channel))

    def command_patterns(self):
        return (
            ('!shutdown', self.shutdown),
            ('!last', self.last),
            ('^http[s]?:\/\/osu\.ppy\.sh\/(b)\/[0-9]+', self.beatmap_request),
        )

class RippleBot(Dispatcher):
    def shutdown(self, nick, message, channel):
        if nick == config["ripple_owner"]:
            quit()
    @cooldown(10)
    def settings(self, nick, message, channel):
        d = danibot.get_user_settings(nick)
        ripple_bot.send("privmsg", target=nick, message="Mode selected: {}, Ingame bot is: {}, Twitch bot is: {}".format(d["mode"], d["osu_bot"], d["twitch_bot"]))
    @cooldown(30)
    def join_twitch(self, nick, message, channel):
        f = danibot.user_settings(nick)
        twitch_bot.send('JOIN', channel=f["twitch_username"])
        ripple_bot.send("privmsg", target=nick, message="AiAeGames joined your twitch channel.")
        twitch_bot.send("privmsg", target=f["twitch_username"], message="o/")
    @cooldown(10)
    def mode(self, nick, message, channel):
        if danibot.find_user(nick) == True:
            mode = ''.join(re.findall('\d+', message))
            if "0" <= mode <= "3":
                danibot.mode_update(mode, nick)
                ripple_bot.send("privmsg", target=nick, message="Mode is set to {}.".format(mode))
            else:
                ripple_bot.send("privmsg", target=nick, message="0 - Standard, 1 - Taiko, 2 - CtB and 3 - Mania")
    
    @cooldown(10)
    def stalk(self, nick, message, channel):
        arg = re.findall("(twitch|ingame)", message)
        if not arg:
            ripple_bot.send("privmsg", target=channel, message="No option selected.")
        else:
            danibot.bot_update(arg[0], nick)
            d = danibot.get_user_settings(nick)
            ripple_bot.send("privmsg", target=nick, message="Ingame bot is: {}, Twitch bot is: {}".format(d["osu_bot"], d["twitch_bot"]))

    @cooldown(10)
    def update(self, nick, message, channel):
        ripple_bot.send("privmsg", target=nick, message=danibot.user_update(nick))

    @cooldown(10)
    def track(self, nick, message, channel):
        r = ripple.user(name=nick)
        if danibot.find_user(nick) == True:   
            ripple_bot.send("privmsg", target=nick, message="You are already signed up for tracking.")
        else:
            cursor.execute("INSERT INTO ripple_tracking (user_id, username, twitch_username, mode, osu_bot, twitch_bot, std_rank, std_pp, taiko_rank, taiko_score, ctb_rank, ctb_score, mania_rank, mania_pp) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [r["id"], r["username"], "", 0, 0, 0, r["std"]["global_leaderboard_rank"], r["std"]["pp"], r["taiko"]["global_leaderboard_rank"], r["taiko"]["ranked_score"], r["ctb"]["global_leaderboard_rank"], r["ctb"]["ranked_score"], r["mania"]["global_leaderboard_rank"], r["mania"]["pp"]])
            connection.commit()
            ripple_bot.send("privmsg", target=nick, message="Thanks for using my bot :).")
    @cooldown(10)
    def help(self, nick, message, channel):
        ripple_bot.send("privmsg", target=nick, message="[http://danibot.tk/ Commands] -- Note every command have cooldown 10 secounds!")

    def command_patterns(self):
        return (
            ('!shutdown', self.shutdown),
            ('!stalk', self.track),
            ('!settings', self.settings),
            ('!twitch', self.join_twitch),
            ('!update', self.update),
            ('!mode', self.mode),
            ('!bot', self.stalk),
            ('!help', self.help),
        )

ripple_dispatcher = RippleBot(ripple_bot)
twitch_dispatcher = TwitchBot(twitch_bot)
connector(ripple_bot, ripple_dispatcher, config["ripple_username"], ["#bulgarian"], config["ripple_password"])
connector(twitch_bot, twitch_dispatcher, config["twitch_username"], ["#danidpp", "#bloodline97", "#cadencelg"], config["twitch_password"])
ripple_bot.loop.create_task(autoupdate())
ripple_bot.loop.create_task(ripple_bot.connect())
ripple_bot.loop.create_task(twitch_bot.connect())
ripple_bot.loop.run_forever()