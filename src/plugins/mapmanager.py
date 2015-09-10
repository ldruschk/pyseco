from plugins.pyseco_plugin import pyseco_plugin
import os
from xmlrpc.client import Fault


class mapmanager(pyseco_plugin):
    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco, db=True)
        self.register_chat_command("add")

        self.initialize()

    def initialize(self):
        response = self.pyseco.query((),"GetMapsDirectory")
        self.map_dir = response[0][0]
        self.config_path = os.path.join(self.map_dir, "MatchSettings", "pyseco.txt")

        response = self.pyseco.query((self.config_path, ), "LoadMatchSettings")
        if isinstance(response, Fault):
            self.error_log("Could not load GameData: %s" % self.config_path)
            self.console_log("Saving current GameData as %s" % self.config_path)
            response = self.pyseco.query((self.config_path, ), "SaveMatchSettings")

    def process_callback(self, value):
        pass

    def process_chat_command(self, command, params, login, admin, mod):
        print(command, params, login, admin, mod)
