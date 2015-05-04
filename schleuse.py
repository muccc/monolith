#! /usr/bin/env python

import irc.bot
import irc.client
import irc.strings
import socket
import ssl
import threading
import Queue
import time
import re
import BaseHTTPServer
import SocketServer
import json
import logging

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
        self.debug = True

    def start(self):
        while True:
            try:
                irc.bot.SingleServerIRCBot.start(self)
            except irc.client.ServerNotConnectedError:
                print 'Lost connection to server. Restarting'
            except:
                import traceback
                print traceback.format_exc()


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
        if self.debug: print "Setting topic to " + topic
        self.connection.topic(self.channel, topic)

    def message_check(self):
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
                print "received: " + data

            #if data == "public":
            #    data = "party"

            self.doorstate = data

            if self.topic:
                if self.debug: print "got a topic %s" % self.topic
                m = re.match(r'\bclub\b (\b\w*\b)', self.topic)
                if not m:
                    return
                self.channelstate = m.group(1)
                if self.debug: print 'matched ' + self.channelstate

                print "channelstate: " + self.channelstate
                print "doorstate: " + self.doorstate
                if self.channelstate != self.doorstate:
                    print "replacing topic"
                    #bot.setTopic(bot.getTopic().replace(/hq.*?\|/g, doorstate + " |"));
                    #bot.say(bot.getTopic().replace(/\bhq\b \b\w*\b/, doorstate));
                    new_topic = re.sub(r'\bclub\b \b\w*\b', "club " + self.doorstate, self.topic)
                    self.setTopic(new_topic)

    def on_topic(self, c, e):
        if e.type == 'currenttopic':
            self.topic = e.arguments[1]
        elif e.type == 'topic':
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

class SchleuseUDP(threading.Thread):
    UDP_IP = "0.0.0.0"
    UDP_PORT = 2080

    def __init__(self, consumer):
        threading.Thread.__init__(self)
        self.consumer = consumer

    def run(self):
        sock = socket.socket(socket.AF_INET, # Internet
                socket.SOCK_DGRAM) # UDP
        sock.bind((self.UDP_IP, self.UDP_PORT))

        while True:
            data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
            try:
                self.consumer.put((data, addr), False)
            except:
                pass
            #print "received message:", data

class DoorstateHTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        global bot
        s.send_response(200)
        s.send_header('Content-type', 'text/plain')
        s.send_header('Cache-Control', 'max-age=0, no-cache, no-store, must-revalidate')
        s.send_header('Pragma','no-cache')
        s.end_headers()
        s.wfile.write(bot.doorstate + '\n')

class DoorstateHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        global bot
        self.request.sendall(bot.doorstate + '\n')

class SpaceAPIHTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        global bot
        s.send_response(200)
        s.send_header('Content-type', 'text/json')
        s.send_header('Cache-Control', 'max-age=0, no-cache, no-store, must-revalidate')
        s.send_header('Pragma','no-cache')
        s.end_headers()

        apistub = {
            "api":"0.12",
            "space":"CCC Munich",
            "logo":"http://muc.ccc.de/lib/tpl/muc3/images/muc3_klein.gif",
            "icon":{
                "open":"http://www.chaostreff-dortmund.de/green.png",
                "closed":"http://www.chaostreff-dortmund.de/red.png"
            },
            "url":"http://muc.ccc.de/",
            "address":"Schleissheimer Str. 41, 80797 Muenchen, Germany",
            "contact":{
                "irc":"ircs://irc.darkfasel.net/#ccc",
                "twitter":"@muccc",
                "email":"info@muc.ccc.de",
                "ml":"talk@lists.muc.ccc.de"
            },
            "lat":48.15370,
            "lon":11.560801,
            "open":False
        }

        if bot.doorstate == bot.doorstate_open or bot.doorstate == 'public':
            apistub['open'] = True

        s.wfile.write(json.dumps(apistub))

bot = None

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

    message_queue = Queue.Queue(5)

    bot = SchleuseBot(channel, nickname, server, message_queue, port)
    bot_thread = threading.Thread(target=bot.start)
    bot_thread.start()
    SchleuseUDP(message_queue).start()

    doorstate_http_server = BaseHTTPServer.HTTPServer(('0.0.0.0', 8080), DoorstateHTTPHandler)
    doorstate_http_server_thread = threading.Thread(target=doorstate_http_server.serve_forever)
    doorstate_http_server_thread.setDaemon(True)
    doorstate_http_server_thread.start()

    space_api_http_server = BaseHTTPServer.HTTPServer(('0.0.0.0', 8081), SpaceAPIHTTPHandler)
    space_api_http_server_thread = threading.Thread(target=space_api_http_server.serve_forever)
    space_api_http_server_thread.setDaemon(True)
    space_api_http_server_thread.start()

    doorstate_server = BaseHTTPServer.HTTPServer(('0.0.0.0', 8001), DoorstateHandler)
    doorstate_server_thread = threading.Thread(target=doorstate_server.serve_forever)
    doorstate_server_thread.setDaemon(True)
    doorstate_server_thread.start()


    bot_thread.join()

if __name__ == "__main__":
    FORMAT = '%(asctime)-15s %(levelname)s: %(module)s:%(funcName)s(): %(message)s'
    logging.basicConfig(level = logging.DEBUG, format = FORMAT)
    main()
