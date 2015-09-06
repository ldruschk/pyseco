import sys
import json
import datetime

from threading import Thread, Event
from xmlrpc.client import Fault

from gbxremote import GBX2xmlrpc

class PySECO(GBX2xmlrpc):
    def __init__(self, config_file):
        GBX2xmlrpc.__init__(self)
        self.callback_listeners = dict()
        self.listeners = dict()
        self.responses = dict()

        self.load_config(config_file)
        try:
            server_ip = self.config["server"]["ip"]
            server_port = self.config["server"]["port"]
            if not self.connect(server_ip, server_port):
                self.error_log("Failed to conect to %s:%d" % (server_ip, server_port), True)
            self.console_log("Connected to %s:%d" % (server_ip, server_port))

            if not self.auth(self.config["authorization"]["name"], self.config["authorization"]["password"]):
                self.error_log("Failed to authenticate - Continuing without authorization")
            if self.config["xmlrpc_enableCallbacks"]:
                self.enable_callbacks()
        except KeyError as e:
            print("Setting not found: %s" % str(e))
            self.shutdown()
            sys.exit(1)

    def load_config(self, config_file):
        try:
            with open(config_file) as data_file:
                data = json.load(data_file)
            self.config = data
        except FileNotFoundError:
            print("Config file not found: %s" % config_file)
            sys.exit(1)
        except ValueError:
            print("Invalid json in config file: %s" % config_file)
            sys.exit(1)
        except Exception as e:
            print(type(e))

    def query(self, params, methodName):
        handler = self.send(params,methodName)
        event = Event()
        self.add_listener(handler, event)
        while 1:
            value = self.get_response(handler)
            if value:
                break
            event.wait()

        return value

    def add_callback_listener(self, methodName, listener):
        if not methodName in self.callback_listeners:
            self.callback_listeners[methodName] = []
        self.callback_listeners[methodName].add(listener)

    def notify_callback_listeners(self, value):
        if value[1] in self.callback_listeners:
            for listener in self.callback_listeners[value[1]]:
                listener.callback_notify(value)

    def auth(self, username, password):
        out = self.query((username,password),"Authenticate")
        if isinstance(out, Fault):
            return False
        return out

    def enable_callbacks(self):
        return self.query((True,),"EnableCallbacks")

    def add_listener(self, handler, event):
        self.listeners[handler] = event

    def get_response(self, handler):
        return self.responses.pop(handler, None)

    def handle(self, value, handle):
        # Response to a query
        if handle >= 0x80000000:
            self.responses[handle] = value
            if handle in self.listeners:
                self.listeners[handle].set()
            return

        if isinstance(value, Fault):
            print("XML-RPC error")
            print(value.faultCode)
            print(value.faultString)
            return

        self.notify_callback_listeners(value)
        print(value)

    def error_log(self, string, fatal = False):
        self.console_log("[Error] " + string)
        if fatal:
            self.console_log("[Error] Fatal error. Shutting down")
            self.shutdown()
            sys.exit(1)

    def console_log(self, string):
        print(("[%s] " % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + string)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 pyseco.py <config.json>")
        sys.exit(1)
    pyseco = PySECO(sys.argv[1])
    while 1:
        try:
            text = input()
            print(pyseco.query((300,0),text))
            #pygbx.send((),text)
            #pygbx.send(("the_legend_of_master",),text)
            #pygbx.send((text,),"ChatSendServerMessage")
        except KeyboardInterrupt:
            pyseco.shutdown()
            break
