#!/usr/bin/python3

import MQTTV3112 as MQTTV3
import traceback, datetime, os, sys, select, binascii
import time, traceback
import math
import socketserver
import json

import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# create logger with 'spam_application'
logger = logging.getLogger('seeed_3thMqtt')
logger.setLevel(logging.INFO)
# create file handler which logs even debug messages
# fh = RotatingFileHandler('logs/_3mq_data.log', maxBytes=102400, backupCount=20)
fh = TimedRotatingFileHandler('./logs/seeed_3mq.log', when='midnight', backupCount=20)
fh.setLevel(logging.INFO)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


# Message types
CONNECT, CONNACK, PUBLISH, PUBACK, PUBREC, PUBREL, \
PUBCOMP, SUBSCRIBE, SUBACK, UNSUBSCRIBE, UNSUBACK, \
PINGREQ, PINGRESP, DISCONNECT = range(1, 15)

Username = 'seeed'
Passwd = b'sensecap'

def timestamp():
    now = datetime.datetime.now()
    return now.strftime('%Y%m%d %H%M%S')+str(float("."+str(now.microsecond)))[1:]


class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        if not hasattr(self, "ids"):
          self.ids = {}
        if not hasattr(self, "versions"):
          self.versions = {}
        inbuf = True
        terminated = False
        client = self.request
        #while inbuf != None and not terminated:
        while inbuf != None and not terminated:
            try:
                inbuf = MQTTV3.getPacket(client) # get one packet
                packet = MQTTV3.unpackPacket(inbuf)
                if packet.fh.MessageType == MQTTV3.CONNECT:
                    self.ids[id(client)] = packet.ClientIdentifier
                    self.versions[id(client)] = 3
                    logger.debug("{} {}".format(self.ids[id(client)], repr(packet)))
                    '''
                        Check user name and passwd, device must be authorized by username and password
                    '''
                    logger.debug('Username={} passwd={}'.format(packet.username, packet.password))
                    if packet.username == Username and packet.password == Passwd:
                        logger.info("Device {} authorized!".format(self.ids[id(client)]))
                    else:
                        logger.error("Username or password invalid")
                        terminated = True
                        break
                    # Send downlink command
                    dl_str = '{\"type\":2,\"tmst\":\"' + '{}'.format(math.ceil(time.time()*1000)) + '\",\"intv\":300}'
                    downlinkconf = bytes(dl_str, 'utf-8')
                    client.sendall(downlinkconf)
                    logger.info('Send {}'.format(downlinkconf))
                elif packet.fh.MessageType == MQTTV3.PUBLISH:
                    # Parse turn code
                    logger.debug("{} {}".format(self.ids[id(client)], repr(packet)))
                    json_obj = json.loads(packet.data)
                    if json != None:
                        logger.info('{}'.format(json_obj))
                    else:
                        logger.error("Decode json fail.")
                    
                elif packet.fh.MessageType == MQTTV3.DISCONNECT:
                    logger.debug("{} {}".format(self.ids[id(client)], repr(packet)))
                    logger.info("{} {}".format(self.ids[id(client)], " connection closing"))
                    client.close()
                    terminated = True
            except:
                terminated = True

class MyThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 1884
    
    logger.info("Listening on {} port {}".format(HOST, PORT))

    server = MyThreadingTCPServer((HOST, PORT), MyTCPHandler)
    server.serve_forever()
