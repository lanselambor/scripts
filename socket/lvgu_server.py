#!/usr/bin/python 

from __future__ import print_function

import SocketServer, time, sys
import binascii
import logging
from logging.handlers import RotatingFileHandler

# create logger with 'spam_application'
logger = logging.getLogger('lvgu_data_logger')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
# fh = logging.FileHandler('lvgu_data.log')
fh = RotatingFileHandler('logs/lvgu_data.log', maxBytes=102400, backupCount=20)
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


def getPacket(aSocket):
    "receive the next packet"
    buf = aSocket.recv(1) # get the first byte fixed header
    if buf != b"\xaa":
        return None
    if str(aSocket).find("[closed]") != -1:
        closed = True
    else:
        closed = False
    if closed:
        return None
    # now get the remaining length
    multiplier = 1
    remlength = 0
    next = aSocket.recv(1)
    # print("packet len={}".format(binascii.hexlify(next)))
    buf += next
    pLen = ord(buf[-1:])
    remlength = pLen - 2  # ? why decrease by 3
    # receive the remaining length if there is any
    rest = bytes()
    if remlength > 0:
        while len(rest) < remlength:
            rest += aSocket.recv(remlength-len(rest))
    # checksum
    xor = pLen
    for d in rest[0:-2]:
        xor ^= ord(d)
    # print('checksum', xor, ord(rest[-2]))
    if xor != ord(rest[-2]):
        logger.error('Packet checksum invalid!');
        return None
    return buf + rest

def parse_binary(packet):
    head = packet[0]
    if head != b'\xaa':
        return None
    length = ord(packet[1])
    opt = packet[2:3]
    cmd = packet[3:4]
    gmac = packet[4:10]
    nmac = packet[10:14]
    data = packet[14:-2]
    crc = packet[-2]
    tail = packet[-1]
    # print("soh={} length={} opt={} cmd={} gmac={} nmac={} data={} crc={} tail={}".format(toHex(head), length, toHex(opt), toHex(cmd), gmac, nmac, toHex(data), toHex(crc), toHex(tail)))
    i = 0
    step = 0
    value = 0
    stype = 0
    for d in data:
        if step == 0:
            stype = ord(d) + 4096
            step += 1
        elif step < 4:
            value |=  ord(d) << (8*i)
            step += 1
            i += 1
        else:
            value |=  ord(d) << (8*i)
            logger.info('{} {}={:.3f}'.format(toHex(gmac), stype, value/1000.0))
            step = 0
            value = 0
            i = 0

#convert string to hex
def toHex(s):
    lst = []
    for ch in s:
        hv = hex(ord(ch)).replace('0x', '')
        if len(hv) == 1:
            hv = '0'+hv
        # hv = hv + ' '
        lst.append(hv)
    
    return reduce(lambda x,y:x+y, lst)

class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        client = self.request
        terminate = False
        inbuf = True
        # logger.info("New connection from {}".format(self.client_address[0]))
        while inbuf != None and not terminate:
            try:
                inbuf = getPacket(client)
                # print('[{}]< '.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())), end='')
                # print('{}'.format(toHex(inbuf)))
                if inbuf != None:
                    parse_binary(inbuf);
            except Exception as e:
                print(e)
                client.close()
                terminate = True
        # print('{} Disconnected!'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))


class MyThreadingTCPServer(SocketServer.ThreadingTCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 9632
    print('{} Start local TCP sever at port {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), PORT))

    server = MyThreadingTCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
