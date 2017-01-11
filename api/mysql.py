from api import generator, osu, ripple, tillerino, twitch, mysql
import json
import asyncio
import bottom
import requests
import pymysql
import re

with open("/home/aiae/r/config.json", "r") as f: 
    config = json.load(f)

connection = pymysql.connect(host=config['host'], user=config['user'], passwd=config['password'], db=config['database'])
connection.autocommit(True)
cursor = connection.cursor(pymysql.cursors.DictCursor)

def execute(sql, args=None):
    global connection
    global cursor
    try:
        cursor.execute(sql, args) if args is not None else cursor.execute(sql)
        return cursor
    except pymysql.err.OperationalError:
        print ("Something went wrong with mysql connection.... trying to reconnect.")
        connection.connect()
        return execute(sql, args)

def checker(user_id=None, username=None):
    if user_id != None:
        execute("SELECT * FROM ripple WHERE user_id=%s", [user_id])
    else:
        execute("SELECT * FROM ripple WHERE username=%s", [username])
    counter = cursor.fetchone()
    if counter != None and len(counter) > 0:
        return True
    else:
        return False

def check_mp(mp):
    execute("SELECT * FROM mp WHERE channel=%s", [mp])
    counter = cursor.fetchone()
    if counter != None and len(counter) > 0:
        return True
    else:
        return False