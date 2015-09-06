from gbxremote import GBX2xmlrpc

class PySECO(GBX2xmlrpc):
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
    pyseco = PySECO(server_ip, server_port)
    pyseco.auth(username,password)
    pyseco.enableCallbacks()
    while 1:
        try:
            text = input()
            pyseco.send((300,0),text)
            #pygbx.send((),text)
            #pygbx.send(("the_legend_of_master",),text)
            #pygbx.send((text,),"ChatSendServerMessage")
        except KeyboardInterrupt:
            break
