#! /usr/bin/env python

import sys
sys.path.append("/home/schleuse/build/irc/build/lib.linux-x86_64-2.7")
sys.path.append("/home/schleuse/pyschleuse/lib/python2.7/site-packages")
sys.path.append("/home/schleuse/build/irc")
sys.path.append("/home/schleuse/build/six")
sys.path.append("/home/schleuse/build/jaraco.util")

import ssl
import time
import logging
import threading

try:
    from urllib import urlopen
except:
    from urllib.request import urlopen

bot = None
debug = False

def log_null(self, format, *args):
    pass

def main():
    global bot
    import sys
    if len(sys.argv) != 4:
        print("Usage: schleuse <server[:port]> <channel> <nickname>")
        sys.exit(1)

    s = sys.argv[1].split(":", 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print("Error: Erroneous port.")
            sys.exit(1)
    else:
        port = 6697
    channel = sys.argv[2]
    nickname = sys.argv[3]

    # start IRC bot
    bot = SchleuseBot(channel, nickname, server, irc_bot_message_queue, port)
    bot_thread = threading.Thread(target=bot.start)
    bot_thread.start()

    # join irc bot thread
    bot_thread.join()


## IRC Bot
import json
import re
import irc.bot
import irc.client
import irc.strings

# Work around decoding invalid UTF-8
irc.client.ServerConnection.buffer_class.errors = 'replace'

class SchleuseBot(irc.bot.SingleServerIRCBot):
    doorstate_closed = "closed"
    doorstate_open = "open"

    def __init__(self, channel, nickname, server, message_queue, port=6697):
        ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname, connect_factory=ssl_factory)
        self.channel = channel
        self.message_queue = message_queue
        self.lastSchlaubergerTime = 0
        self.ringCounter = 0
        self.lastRingDate = 0
        self.doorstate = "fnord"
        self.topic = None
        self.debug = debug
        self.nextevent = None
        self.topic_block = False
        self.t0 = time.time()

    def start(self):
        while True:
            try:
                irc.bot.SingleServerIRCBot.start(self)
            except irc.client.ServerNotConnectedError:
                print('Lost connection to server. Restarting')
            except:
                import traceback
                print(traceback.format_exc())


    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.add_global_handler("currenttopic", self.on_topic)
        c.execute_every(1, self.message_check)
        c.join(self.channel)
        while not self.message_queue.empty():
            self.message_queue.get()

    def notice(self, msg):
        self.connection.privmsg(self.channel, msg)

    def setTopic(self, topic):
        if self.debug: print("Setting topic to " + topic)
        self.connection.topic(self.channel, topic)

    def message_check(self):
        nextevent = json.load(urlopen('http://api.muc.ccc.de/nextevent.json'))
        nextevent_topic = 'next event: %s %s %s %s' % (nextevent['weekday'], nextevent['date'], nextevent['time'], nextevent['name'])
        new_topic = re.sub(r'next event:[^|]*(?= |$)', nextevent_topic , self.topic)
        if new_topic != self.topic and not self.topic_block:
            print("wegen " + new_topic + " und " + self.topic)
            self.setTopic(new_topic)
            self.topic_block = True

        while not self.message_queue.empty():
            data, addr = self.message_queue.get()
            data = data.strip()
            #print data, addr

            if addr[0] != '83.133.178.68' or addr[1] != 2080:
                if time.time() - self.lastSchlaubergerTime > 60:
                    self.lastSchlaubergerTime = time.time()
                    msg = 'irgendein schlauberger (von ' + addr[0] + ':' + str(addr[1]) + ') '
                    msg += 'versucht gerade den tuerstatus zu manipulieren...'
                    self.notice(msg)
                return

            if data == "b" or data == "B":
                self.ringCounter += 1

                if time.time() - self.lastRingDate > 60 and self.doorstate == self.doorstate_closed:
                    self.lastRingDate = time.time()
                    self.notice("jemand klingelt an der haustuer.");
                return

            if self.debug or data != self.doorstate:
                print("received: " + data)

            #if data == "public":
            #    data = "party"

            self.doorstate = data

        if self.topic:
            self.topic_block = False
            if self.debug: print("got a topic %s" % self.topic)
            m = re.match(r'\bclub\b (\b\w*\b)', self.topic)
            if not m:
                return
            self.channelstate = m.group(1)
            if self.debug: print('matched ' + self.channelstate)

            if self.channelstate != self.doorstate:
                print("channelstate: " + self.channelstate)
                print("doorstate: " + self.doorstate)
                print("replacing topic")
                #bot.setTopic(bot.getTopic().replace(/hq.*?\|/g, doorstate + " |"));
                #bot.say(bot.getTopic().replace(/\bhq\b \b\w*\b/, doorstate));
                new_topic = re.sub(r'\bclub\b \b\w*\b', "club " + self.doorstate, self.topic)
                self.setTopic(new_topic)
        
        t = time.time()
        dt = t - self.t0
        self.t0 = t

        #print "delta t", dt
        if dt < 1:
            time.sleep(1-dt) # WTF fix for back to back message_check() scheduling

    def on_topic(self, c, e):
        if e.type == 'currenttopic':
            print("currenttopic", e.arguments[1])
            self.topic = e.arguments[1]
        elif e.type == 'topic':
            print("topic", e.arguments[0])
            self.topic = e.arguments[0]

"""
    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
        a = e.arguments[0].split(":", 1)
        if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(self.connection.get_nickname()):
            self.do_command(e, a[1].strip())
        return

    def do_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection
"""

if __name__ == "__main__":
    FORMAT = '%(asctime)-15s %(levelname)s: %(module)s:%(funcName)s(): %(message)s'
    logging.basicConfig(level = logging.DEBUG if debug else logging.INFO, format = FORMAT)
    main()
