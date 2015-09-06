import sys
import json
import datetime
import importlib
import copy

from db import PySECO_DB, DBException
from threading import Thread, Event
from xmlrpc.client import Fault

from gbxremote import GBX2xmlrpc

class Player():
    def __init__(self, dict):
        self.login = dict["Login"]
        self.nick_name = dict["NickName"]
        self.is_spectator = dict["IsSpectator"]
        self.player_id = dict["PlayerId"]
        self.is_in_official_mode = dict["IsInOfficialMode"]
        self.ladder_ranking = dict["LadderRanking"]

    def modify(self, dict):
        self.login = dict["Login"]
        self.nick_name = dict["NickName"]
        self.is_spectator = dict["IsSpectator"]
        self.player_id = dict["PlayerId"]
        self.is_in_official_mode = dict["IsInOfficialMode"]
        self.ladder_ranking = dict["LadderRanking"]

class PySECO(GBX2xmlrpc):
    def __init__(self, config_file):
        GBX2xmlrpc.__init__(self)
        self.callback_listeners = dict()
        self.listeners = dict()
        self.responses = dict()
        self.players = dict()

        self.load_config(config_file)
        try:
            server_ip = self.config["server"]["ip"]
            server_port = self.config["server"]["port"]
            if not self.connect(server_ip, server_port):
                self.error_log("Failed to conect to %s:%d" % (server_ip, server_port), True)
            self.console_log("Connected to %s:%d" % (server_ip, server_port))

            mysql_host = self.config["mysql"]["host"]
            mysql_login = self.config["mysql"]["login"]
            mysql_password = self.config["mysql"]["password"]
            mysql_database = self.config["mysql"]["database"]
            if not self.connect_db(mysql_host, mysql_login, mysql_password, mysql_database):
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

    def connect_db(self, host, login, password, database):
        try:
            self.db = PySECO_DB(host,login,password,database)
            return True
        except Exception as e:
            self.error_log("[DB] %s" % str(e))
            return False

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
            #print(pyseco.query((300,0),text))
            #pyseco.send((),text)
            print(pyseco.query((),text))
            #pygbx.send(("the_legend_of_master",),text)
            #pygbx.send((text,),"ChatSendServerMessage")
        except KeyboardInterrupt:
            pyseco.shutdown()
            break
