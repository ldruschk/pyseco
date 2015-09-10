from plugins.pyseco_plugin import pyseco_plugin
import os
from xmlrpc.client import Fault
import urllib.request
import json


class DownloadError(Exception):
    def __init__(self):
        Exception.__init__(self)


class mapmanager(pyseco_plugin):
    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco, db=True)
        self.register_chat_command("add")
        self.register_chat_command("remove")
        self.register_callback("TrackMania.ChallengeListModified")

        self.initialize()

    def initialize(self):
        response = self.pyseco.query((),"GetMapsDirectory")
        self.map_dir = response[0][0]
        self.config_path = os.path.join(self.map_dir, "MatchSettings", "pyseco.txt")
        self.download_dir = os.path.join(self.map_dir, "Downloaded")

        response = self.pyseco.query((self.config_path, ), "LoadMatchSettings")
        if isinstance(response, Fault):
            self.error_log("Could not load MatchSettings: %s" % self.config_path)
            self.save_matchsettings()

    def save_matchsettings(self):
        self.console_log("Saving current MatchSettings as %s" % self.config_path)
        self.pyseco.query((self.config_path, ), "SaveMatchSettings")

    def process_callback(self, value):
        if value[1] == "TrackMania.ChallengeListModified":
            self.save_matchsettings()

    def mx_download(self, tid, uid):
        map_path = os.path.join(self.download_dir, uid+".gbx")
        # File already exists
        if os.path.isfile(map_path):
            return map_path
        url = "http://tm.mania-exchange.com/tracks/download/%s" % tid

        with open(map_path, "wb") as f:
            request = urllib.request.urlopen(url)
            content = request.read()
            code = request.getcode()
            request.close()
            if code != 200:
                raise DownloadError()

            f.write(content)

        return map_path

    def add_from_mx(self, id):
        url = "http://api.mania-exchange.com/tm/maps/%s" % str(id)
        request = urllib.request.urlopen(url)
        content = request.read()
        code = request.getcode()
        request.close()
        if code != 200:
            return

        info = json.loads(content.decode())

        # Invalid ID
        if not info:
            return

        map_info = info[0]

        tid = map_info["TrackID"]
        uid = map_info["TrackUID"]
        # Download map if not exists
        path = self.mx_download(tid, uid)

        response = self.pyseco.query((path, ), "AddMap")

    def remove_current(self):
        response = self.pyseco.query((), "GetCurrentMapInfo")
        filename = response[0][0]["FileName"]
        response = self.pyseco.query((filename, ), "RemoveMap")

    def process_chat_command(self, command, params, login, admin, mod):
        if command == "add" and (admin or mod):
            for id_ in params:
                self.add_from_mx(id_)
        if command == "remove" and (admin or mod):
            if len(params) == 0:
                self.remove_current()
