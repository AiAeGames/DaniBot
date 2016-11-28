import re
import asyncio
import threading


def connector(bot, dispatcher, NICK, CHANNELS, PASSWORD=None):
    @bot.on('CLIENT_CONNECT')
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

    @bot.on('PING')
    def keepalive(message, **kwargs):
        bot.send('PONG', message=message)

    @bot.on('PRIVMSG')
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
            match = pattern.match(message) or pattern.match('/privmsg')
            if match:
                # print(match.groupdict())
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
    def __init__(self, Time=None, user=""):
        self.Time = Time if Time or Time == 0 and type(Time) == int else 5
        self.Locked = False

    def Lock(self):
        if not self.Locked:
            if self.Time > 0:
                self.Locked = True
                t = threading.Timer(self.Time, self.Unlock, ())
                t.daemon = True
                t.start()
        return self.Locked

    def Unlock(self):
        self.Locked = False
        return self.Locked


def cooldown(delay):
    def decorator(func):
        def get_locker(nick):
            if nick not in func.__cooldowns:
                func.__cooldowns[nick] = Locker(delay)

            return func.__cooldowns[nick]

        def inner(*args, **kwargs):
            nick = args[1]

            if not hasattr(func, "__cooldowns"):
                func.__cooldowns = {}

            user_cd = get_locker(nick)
            if user_cd.Locked:
                #return "You cannot use this command yet."
                return

            ret = func(*args, **kwargs)
            user_cd.Lock()
            return ret
        return inner

    return decorator
