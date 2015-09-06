#import xmlrpc.client
import socket
import threading
from xmlrpc.client import loads, dumps, Fault
from lxml import etree

class Request():
    def __init__(self, methodName, params):
        self.methodName = methodName
        self.params = params

    def toString(self):
        methodCall = etree.Element("methodCall")
        methodName = etree.Element("methodName")
        methodName.text = self.methodName
        methodCall.append(methodName)
        methodCall.append(etree.Element("params"))

        return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>".encode() + etree.tostring(methodCall, encoding="utf-8")

class GBX2xmlrpc():
    def __init__(self):
        self.handler = 0x80000000

    def connect(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_ip,self.server_port))

        four = self.socket.recv(4)
        protocol = self.socket.recv(11)

        if protocol.decode() != "GBXRemote 2":
            print("Not a TM Server")

        #print("Starting listener Thread")

        self.thread = threading.Thread(target=self.listen)
        self.thread.start()

    def send(self, params, methodName):
        brequest = dumps(params,methodname=methodName).encode()
        #print(brequest)
        blength = len(brequest).to_bytes(4,byteorder='little')
        #print(blength)
        bhandler = self.handler.to_bytes(4,byteorder='little')
        #print(self.handler)
        self.handler += 1

        self.socket.send(blength + bhandler + brequest)

    def listen(self):
        while 1:
            try:
                size = int.from_bytes(self.socket.recv(4),byteorder="little")
                hndl = int.from_bytes(self.socket.recv(4),byteorder="little")
                answer = self.socket.recv(size)
                #print(answer.decode())

                try:
                    (data, methodName) = loads(answer,use_builtin_types=True)
                    self.handle(data, methodName = methodName, handle = hndl)
                except Fault as e:
                    self.handle(e)
            except KeyboardInterrupt:
                break
        self.socket.close()

    def handle(self, input):
        pass

    # 32-bit little-endian
    def toInt(self, val):
        return (val[0] & 0xff) | ((val[1] & 0xff) << 8) | ((val[2] & 0xff) << 16) | ((val[3] & 0xff) << 24)

class GBXRemote(GBX2xmlrpc):
    def __init__(self, server_ip, server_port):
        GBX2xmlrpc.__init__(self)
        self.connect(server_ip, server_port)

    def auth(self, username, password):
        self.send((username,password),"Authenticate")

    def enableCallbacks(self):
        self.send((True,),"EnableCallbacks")

    def handle(self, value, methodName = "", handle = -1):
        if isinstance(value, Fault):
            print("XML-RPC error")
            print(value.faultCode)
            print(value.faultString)
            return
        print(methodName)
        #print(handle)
        print(value)




username = "SuperAdmin"
password = "SuperAdmin"
server_ip = "192.168.178.156"
server_port = 5000

if __name__ == "__main__":
    pygbx = GBXRemote(server_ip, server_port)
    pygbx.auth(username,password)
    pygbx.enableCallbacks()
    while 1:
        try:
            text = input()
            pygbx.send(("the_legend_of_master",),text)
            #pygbx.send((text,),"ChatSendServerMessage")
        except KeyboardInterrupt:
            break
