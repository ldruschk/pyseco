import sys
import json
import datetime
import importlib
import copy

from db import PySECO_DB, DBException
from threading import Thread, Event, Lock
from xmlrpc.client import Fault

from gbxremote import GBX2xmlrpc

class Player():
    def __init__(self, data, db):
        self.modify(data)

        self.db_id = db.add_player(self.login, self.nick_name)

    def get_nick_name(self):
        return(bytes(self.nick_name).decode("unicode_escape"))

    def modify(self, data):
        self.login = data["Login"]
        self.nick_name = data["NickName"].encode("unicode_escape")
        self.is_spectator = data["IsSpectator"]
        self.player_id = data["PlayerId"]
        self.is_in_official_mode = data["IsInOfficialMode"]
        self.ladder_ranking = data["LadderRanking"]

class PySECO(GBX2xmlrpc):
    def __init__(self, config_file):
        GBX2xmlrpc.__init__(self)
        self.callback_listeners = dict()
        self.listeners = dict()
        self.responses = dict()
        self.players = dict()

        self.db_lock = Lock()

        self.chat_color = "$f08"

        self.load_config(config_file)
        try:
            server_ip = self.config["server"]["ip"]
            server_port = self.config["server"]["port"]
            if not self.connect(server_ip, server_port):
                self.error_log("Failed to conect to %s:%d" % (server_ip, server_port), True)
            self.console_log("Connected to %s:%d" % (server_ip, server_port))

            self.mysql_host = self.config["mysql"]["host"]
            self.mysql_login = self.config["mysql"]["login"]
            self.mysql_password = self.config["mysql"]["password"]
            self.mysql_database = self.config["mysql"]["database"]
            self.db = self.connect_db()
            if self.db is None:
                self.error_log("Failed to connect to database", True)

            if not self.auth(self.config["authorization"]["name"], self.config["authorization"]["password"]):
                self.error_log("Failed to authenticate - Continuing without authorization")
            # Enable callbacks unless explicitly set to false
            try:
                if self.config["xmlrpc_enableCallbacks"]:
                    self.enable_callbacks()
            except KeyError:
                self.enable_callbacks()

            for plugin in self.config["plugins"]:
                self.enable_plugin(plugin["name"],plugin["settings"])
        except KeyError as e:
            print("Setting not found: %s" % str(e))
            self.shutdown()
            sys.exit(1)

        self.initialize()
        self.console_log("Setup complete")

    def connect_db(self):
        try:
            return PySECO_DB(self, self.mysql_host,self.mysql_login,self.mysql_password,self.mysql_database)
        except Exception as e:
            self.error_log("[DB] %s" % str(e))
            return None

    def get_player(self, login):
        if login not in self.players:
            return None
        return self.players[login]

    def initialize(self):
        self.send((),"SendHideManialinkPage")
        system_info = self.query((),"GetSystemInfo")
        self.server_login = system_info[0][0]['ServerLogin']
        server_options = self.query((),"GetServerOptions")

    def send_chat_message(self, message):
        self.send((message,),"ChatSendServerMessage")

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

    def enable_plugin(self, name, settings):
        try:
            i = importlib.import_module("plugins.%s" % name)
            constructor = getattr(i,name)
            constructor(self)
        except Exception as e:
            print(str(e))
            print(type(e))

    def add_callback_listener(self, methodName, listener):
        if not methodName in self.callback_listeners:
            self.callback_listeners[methodName] = []
        self.callback_listeners[methodName].append(listener)

    def notify_callback_listeners(self, value):
        if value[1] in self.callback_listeners:
            for listener in self.callback_listeners[value[1]]:
                listener.callback_notify(copy.deepcopy(value))

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
        #print(value)

    def error_log(self, string, fatal = False):
        self.console_log("[Error] " + string)
        if fatal:
            self.console_log("[Error] Fatal error. Shutting down")
            self.shutdown()
            sys.exit(1)

    def console_log(self, string):
        print(("[%s] " % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + string)

    def shutdown(self):
        try:
            self.db.close()
        except Exception as e:
            pass
        GBX2xmlrpc.shutdown(self)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 pyseco.py <config.json>")
        sys.exit(1)
    pyseco = PySECO(sys.argv[1])
    while 1:
        try:
            text = input()
            arr = text.split(" ")
            if arr[0] == "NextMap":
                print(pyseco.query((),"NextMap"))
            elif arr[0] == "SetNextMapIndex":
                print(pyseco.query((int(arr[1]),),"SetNextMapIndex"))
            else:
                print(pyseco.query((),text))
        except KeyboardInterrupt:
            pyseco.shutdown()
            break
        except Exception as e:
            print(type(e))
            print(str(e))
