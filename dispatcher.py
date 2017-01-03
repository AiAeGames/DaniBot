import re
import asyncio
import threading
from collections import defaultdict


def connector(bot, dispatcher, NICK, CHANNELS, PASSWORD=None):
    @bot.on('client_connect')
    async def connect(**kwargs):
        bot.send('USER', user=NICK, realname=NICK)

        if PASSWORD:
            bot.send('PASS', password=PASSWORD)

        bot.send('NICK', nick=NICK)

        # Don't try to join channels until the server has
        # sent the MOTD, or signaled that there's no MOTD.
        done, pending = await asyncio.wait(
            [bot.wait("RPL_ENDOFMOTD"),
             bot.wait("ERR_NOMOTD")],
            loop=bot.loop,
            return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel whichever waiter's event didn't come in.
        for future in pending:
            future.cancel()

        for channel in CHANNELS:
            bot.send('JOIN', channel=channel)

    @bot.on('client_disconnect')
    async def reconnect(**kwargs):
        # Wait a second so we don't flood
        await asyncio.sleep(5, loop=bot.loop)

        # Schedule a connection when the loop's next available
        bot.loop.create_task(bot.connect())

        # Wait until client_connect has triggered
        await bot.wait("client_connect")

    @bot.on('ping')
    def keepalive(message, **kwargs):
        bot.send('PONG', message=message)

    @bot.on('privmsg')
    def message(host, target, message, **kwargs):
        if host == NICK:
            # don't process messages from the bot itself
            return

        if target == NICK:
            # private message
            dispatcher.handle_private_message(host, message)
        else:
            # channel message
            dispatcher.handle_channel_message(host, target, message)


class Dispatcher(object):

    def __init__(self, client):
        self.client = client
        self._callbacks = []
        self.register_callbacks()

    def _register_callbacks(self, callbacks):
        """\
        Hook for registering custom callbacks for dispatch patterns
        """
        self._callbacks.extend(callbacks)

    def register_callbacks(self):
        """\
        Hook for registering callbacks with connection -- handled by __init__()
        """
        self._register_callbacks((
            (re.compile(pattern), callback)
            for pattern, callback in self.command_patterns()
        ))

    def _process_command(self, nick, message, channel):
        results = []

        for pattern, callback in self._callbacks:
            match = pattern.search(message) or pattern.search('/privmsg')
            if match:
                results.append(
                    callback(nick, message, channel, **match.groupdict()))

        return results

    def handle_private_message(self, nick, message):
        for result in self._process_command(nick, message, None):
            if result:
                self.respond(result, nick=nick)

    def handle_channel_message(self, nick, channel, message):
        for result in self._process_command(nick, message, channel):
            if result:
                self.respond(result, channel=channel)

    def command_patterns(self):
        """\
        Hook for defining callbacks, stored as a tuple of 2-tuples:

        return (
            ('/join', self.room_greeter),
            ('!find (^\s+)', self.handle_find),
        )
        """
        raise NotImplementedError

    def respond(self, message, channel=None, nick=None):
        """\
        Multipurpose method for sending responses to channel or via message to
        a single user
        """
        if channel:
            if not channel.startswith('#'):
                channel = '#%s' % channel
            self.client.send('PRIVMSG', target=channel, message=message)
        elif nick:
            self.client.send('PRIVMSG', target=nick, message=message)


class Locker(object):
    def __init__(self, delay=None, user=""):
        self.delay = delay if delay or delay == 0 and type(delay) == int else 5
        self.locked = False

    def lock(self):
        if not self.locked:
            if self.delay > 0:
                self.locked = True
                t = threading.Timer(self.delay, self.unlock, ())
                t.daemon = True
                t.start()
        return self.locked

    def unlock(self):
        self.locked = False
        return self.locked


def cooldown(delay):
    def decorator(func):
        if not hasattr(func, "__cooldowns"):
            func.__cooldowns = defaultdict(lambda: Locker(delay))

        def inner(*args, **kwargs):
            nick = args[1]

            user_cd = func.__cooldowns[nick]
            if user_cd.locked:
                return

            ret = func(*args, **kwargs)
            user_cd.lock()
            return ret
        return inner
    return decorator
