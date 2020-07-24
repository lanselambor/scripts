# Trace MQTT traffic
import MQTTV3112 as MQTTV3
import traceback, datetime, os, sys, select, binascii
import socketserver



# Message types
CONNECT, CONNACK, PUBLISH, PUBACK, PUBREC, PUBREL, \
PUBCOMP, SUBSCRIBE, SUBACK, UNSUBSCRIBE, UNSUBACK, \
PINGREQ, PINGRESP, DISCONNECT = range(1, 15)

def timestamp():
    now = datetime.datetime.now()
    return now.strftime('%Y%m%d %H%M%S')+str(float("."+str(now.microsecond)))[1:]

downlinkconf = b'{\"type\":2,\"tmst\":\"131231232123\",\"intl\":3600}'


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
                    print(timestamp() , "C to S", self.ids[id(client)], repr(packet))
                    #conn_ack = MQTTV3.Connacks().pack()
                    #client.sendall(conn_ack)
                    #print(timestamp()+' send: {}'.format(binascii.hexlify(conn_ack)))
                    client.sendall(downlinkconf)
                    print(timestamp()+' send: {}'.format(downlinkconf))
                elif packet.fh.MessageType == MQTTV3.PUBLISH:
                    print(timestamp() , "C to S", self.ids[id(client)], repr(packet))
                    pub_ack = MQTTV3.Pubacks(QoS=1, MsgId=1).pack()
                    print(timestamp() , "C to S", self.ids[id(client)], repr(packet))
                    client.sendall(pub_ack)
                    print(timestamp()+' send: {}'.format(binascii.hexlify(pub_ack)))
                elif packet.fh.MessageType == MQTTV3.DISCONNECT:
                    print(timestamp() , "C to S", self.ids[id(client)], repr(packet))
                    print(timestamp()+" client "+self.ids[id(client)]+" connection closing")
                    client.close()
                    terminated = True
            except:
                terminated = True
                client.close()

class MyThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    HOST, PORT = "makerzoon.com", 1883

    server = MyThreadingTCPServer((HOST, PORT), MyTCPHandler)
    server.serve_forever()
