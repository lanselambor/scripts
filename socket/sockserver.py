from __future__ import print_function

import SocketServer

def send_from(arr, dest):
    view = memoryview(arr).cast('B')
    while len(view):
        nsent = dest.send(view)
        view = view[nsent:]

# def data_analysis():


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
        while not terminate:
            try:
                self.data = client.recv(1024)
                print("{} wrote:".format(self.client_address[0]))
                print('{}'.format(self.data))
                print('{}'.format(toHex(self.data)))
                # client.sendall(conn_ack)
            except:
                client.close()
                terminate = True


class MyThreadingTCPServer(SocketServer.ThreadingTCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    HOST, PORT = "makerzoon.com", 50000

    server = MyThreadingTCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()

