#! /usr/bin/env python3

import socket
import ssl
import time
import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import BaseRequestHandler
from mqtt import MqttConsumer


debug = False
doorstate = None

def log_null(self, format, *args):
    pass

def on_message(client, userdata, message):
    global doorstate
    doorstate = message.payload

def startHTTPServer(address, handler, silence_logging = False):
    server = HTTPServer(address, handler)
    thread = threading.Thread(target=server.serve_forever)
    if silence_logging:
        server.log_message = log_null
    thread.setDaemon(True)
    thread.start()
    return server

# start HTTP endpoints
def main():
    mqtt = MqttConsumer(__file__)
    
    mqtt.client.on_message = on_message

    startHTTPServer(('0.0.0.0', 8001), DoorstateHandler, True)
    startHTTPServer(('0.0.0.0', 8080), DoorstateHTTPHandler, True)
    startHTTPServer(('0.0.0.0', 8081), SpaceAPIHTTPHandler, True)

class DoorstateHandler(BaseRequestHandler):
    def handle(self):
        global doorstate
        self.request.sendall(doorstate + '\n')

class DoorstateHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(s):
        global doorstate
        s.send_response(200)
        s.send_header('Content-type', 'text/plain')
        s.send_header('Cache-Control', 'max-age=0, no-cache, no-store, must-revalidate')
        s.send_header('Pragma','no-cache')
        s.end_headers()
        s.wfile.write(doorstate + '\n')

class SpaceAPIHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(s):
        global doorstate
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
                "open":"https://status.ctdo.de/img/green.png",
                "closed":"https://status.ctdo.de/img/red.png"
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

        if doorstate == 'member' or doorstate == 'public':
            apistub['open'] = True

        s.wfile.write(json.dumps(apistub))

if __name__ == "__main__":
    FORMAT = '%(asctime)-15s %(levelname)s: %(module)s:%(funcName)s(): %(message)s'
    logging.basicConfig(level = logging.DEBUG if debug else logging.INFO, format = FORMAT)
    main()
