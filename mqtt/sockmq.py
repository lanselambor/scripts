import socket
import sys
import MQTTV3112 as MQTTV3
import datetime, os, sys, binascii

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
# sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 60*1000, 30*1000))

# Bind the socket to the address given on the command line
server_name = None
server_port = None
try:
    server_name = sys.argv[1]
    server_port = sys.argv[2]
except:
    pass

# server_address = ('', 1883)
if server_name == None:
    server_name = 'makerzoon.com'
if server_port == None:
    server_port = 1883
server_address = ("makerzoon.com", int(server_port))

print >>sys.stderr, 'starting up on %s port %s' % server_address
sock.bind(server_address)
sock.listen(1)

#convert string to hex
def toHex(s):
    lst = []
    for ch in s:
        hv = hex(ord(ch)).replace('0x', '')
        if len(hv) == 1:
            hv = '0'+hv
        hv = hv + ' '
        lst.append(hv)
    
    return reduce(lambda x,y:x+y, lst)

conn_head = 0x10
pub_head = 0x30
conn_ack = bytearray([0x20, 0x02, 0, 0])
pub_ack = bytearray([0x40, 0x02, 0, 0])

def timestamp():
    now = datetime.datetime.now()
    return now.strftime('%Y%m%d %H%M%S')+str(float("."+str(now.microsecond)))[1:]

while True:
    id = None
    version = None
    terminated = False
    print >>sys.stderr, 'waiting for a connection'
    client, client_address = sock.accept()
    try:
        print >>sys.stderr, 'client connected:', client_address
        while not terminated:
            data = client.recv(1024)
            if data:
                #print >>sys.stderr, "{}: {}".format(client_address, data)
                #print toHex(data)
                packet = MQTTV3.unpackPacket(data)
                if packet.fh.MessageType == MQTTV3.CONNECT:
                    id = packet.ClientIdentifier
                    version = 3
                    print(timestamp() , "C to S", id, repr(packet))
                    conn_ack = bytearray([0x20, 0x02, 0, 0])
                    client.sendall(conn_ack)
                    print(timestamp()+' send: CONNAKC '+binascii.hexlify(conn_ack))
                    #print(timestamp()+' send: {}'.format(binascii.hexlify(conn_ack)))
                elif packet.fh.MessageType == MQTTV3.PUBLISH:
                    pub_ack = bytearray([0x40, 0x02, 0, 0])
                    print(timestamp() , "C to S", id, repr(packet))
                    client.sendall(pub_ack)
                    print(timestamp()+' send: PUBACK '+ binascii.hexlify(pub_ack))
                    #print(timestamp()+' send: {}'.format(binascii.hexlify(pub_ack)))
                elif packet.fh.MessageType == MQTTV3.DISCONNECT:
                    print(timestamp() , "C to S", id, repr(packet))
                    print(timestamp()+" client "+id+" connection closing")
                    terminated = True
                    client.close()
            else:
                break
    finally:
        client.close()
