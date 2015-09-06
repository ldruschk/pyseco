#import xmlrpc.client
import socket
import threading
from xmlrpc.client import loads, dumps, Fault

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

        self.thread = threading.Thread(target=self.listen)
        self.thread.start()

    def send(self, params, methodName):
        brequest = dumps(params,methodname=methodName).encode()
        blength = len(brequest).to_bytes(4,byteorder='little')
        handler = self.handler
        self.handler += 1
        bhandler = handler.to_bytes(4,byteorder='little')

        self.socket.send(blength + bhandler + brequest)
        return handler

    def listen(self):
        while 1:
            try:
                size = int.from_bytes(self.socket.recv(4),byteorder="little")
                hndl = int.from_bytes(self.socket.recv(4),byteorder="little")
                answer = self.socket.recv(size)

                try:
                    (data, methodName) = loads(answer,use_builtin_types=True)
                    self.handle((data, methodName), hndl)
                except Fault as e:
                    self.handle(e, hndl)
            except KeyboardInterrupt:
                break
        self.socket.close()

    def handle(self, input, handle):
        pass
