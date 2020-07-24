import socket
import sys

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
    server_port = 5000
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

while True:
    print >>sys.stderr, 'waiting for a connection'
    connection, client_address = sock.accept()
    try:
        print >>sys.stderr, 'client connected:', client_address
        while True:
            data = connection.recv(1024)
            if data:
                print >>sys.stderr, "{}: {}".format(client_address, data)
                print toHex(data)
                # connection.sendall(data)
                if (ord(data[0])&  0xF0) == conn_head:
                    connection.sendall(conn_ack)
                elif (ord(data[0]) & 0xF0) == pub_head:
                    connection.sendall(pub_ack)
            else:
                break
    finally:
        connection.close()
