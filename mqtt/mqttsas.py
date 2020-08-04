#!/usr/bin/python3

import MQTTV3112 as MQTTV3
import traceback, datetime, os, sys, select, binascii
import time
import math
import socketserver

import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# create logger with 'spam_application'
logger = logging.getLogger('seeed_3mq')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
# fh = logging.FileHandler('lvgu_data.log')
# fh = RotatingFileHandler('logs/_3mq_data.log', maxBytes=102400, backupCount=20)
fh = TimedRotatingFileHandler('./logs/seeed_3mq.log', when='midnight', backupCount=20)
fh.setLevel(logging.INFO)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
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
                    logger.info("C to S {} {}".format(self.ids[id(client)], repr(packet)))
                    conn_ack = MQTTV3.Connacks().pack()
                    client.sendall(conn_ack)
                    logger.info(' send: {}'.format(binascii.hexlify(conn_ack)))
                    # dl_str = '{\"type\":2,\"tmst\":\"' + '{}'.format(math.ceil(time.time()*1000)) + '\",\"intv\":60}'
                    # downlinkconf = bytes(dl_str, 'utf-8')
                    # client.sendall(downlinkconf)                    
                    logger.info('send: {}'.format(downlinkconf))
                elif packet.fh.MessageType == MQTTV3.PUBLISH:
                    # Parse turn code                     
                    logger.info("C to S {} {}".format(self.ids[id(client)], repr(packet)))
                    pub_ack = MQTTV3.Pubacks(QoS=1, MsgId=1).pack()
                    client.sendall(pub_ack)
                    logger.info('S to C: {}'.format(binascii.hexlify(pub_ack)))
                    print(packet.data)
                elif packet.fh.MessageType == MQTTV3.DISCONNECT:
                    logger.info("C to S".format(self.ids[id(client)], repr(packet)))
                    logger.info("client {} {}".format(self.ids[id(client)], " connection closing"))
                    client.close()
                    terminated = True
            except:
                terminated = True
                client.close()

class MyThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 1884
    
    logger.info("Listening on {} port {}".format(HOST, PORT))

    server = MyThreadingTCPServer((HOST, PORT), MyTCPHandler)
    server.serve_forever()
