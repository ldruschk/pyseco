from plugins.pyseco_plugin import pyseco_plugin
import os
from xmlrpc.client import Fault
import urllib.request
import json
import collections


class DownloadError(Exception):
    def __init__(self):
        Exception.__init__(self)


class mapmanager(pyseco_plugin):
    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco, db=True)
        self.register_chat_command("add")
        self.register_chat_command("remove")
        self.register_chat_command("queue")
        self.register_chat_command("drop")
        self.register_chat_command("restart")
        self.register_chat_command("next")
        self.register_callback("TrackMania.ChallengeListModified")
        self.register_callback("TrackMania.EndRound")

        self.chat_color = "$0a0"

        self.map_queue = collections.deque()

        self.allow_save_matchsettings = True

        self.initialize()

    def initialize(self):
        response = self.pyseco.query((),"GetMapsDirectory")
        self.map_dir = response[0][0]
        self.config_path = os.path.join(self.map_dir, "MatchSettings", "pyseco.txt")
        self.download_dir = os.path.join(self.map_dir, "Downloaded")

        response = self.pyseco.query((self.config_path, ), "LoadMatchSettings")
        if isinstance(response, Fault):
            self.error_log("Could not load MatchSettings: %s" % self.config_path)
            self.console_log("Saving MatchSettings disabled")
            self.allow_save_matchsettings = False
            self.save_matchsettings()

    def save_matchsettings(self):
        if not self.allow_save_matchsettings:
            return
        self.console_log("Saving current MatchSettings as %s" % self.config_path)
        self.pyseco.query((self.config_path, ), "SaveMatchSettings")

    def process_callback(self, value):
        if value[1] == "TrackMania.ChallengeListModified":
            self.save_matchsettings()
        elif value[1] == "TrackMania.EndRound":
            ret = self.select_next()
            cb_tup = ((), "pyseco.mapmanager.EndRound")
            response = self.pyseco.query((), "GetNextMapInfo")
            map_name = response[0][0]["Name"]
            if ret is not None:
                self.pyseco.send_chat_message("$i$fff>> %sThe next map will be "
                        "$z%s$z$s $i%sas requested by: $z$s%s" %
                        (self.chat_color, map_name,
                         self.chat_color, ret))
            else:
                self.pyseco.send_chat_message("$i$fff>> %sThe next map will be "
                        "$z%s" % (self.chat_color, map_name))
            self.pyseco.notify_callback_listeners(cb_tup)

    def select_next(self):
        if not self.map_queue:
            return None

        tup = self.map_queue.popleft()
        print(self.pyseco.query((tup[0], ), "ChooseNextMap"))
        return tup[2]

    def queue_map(self, id_, login, permission):
        # Mods/Admins are allowed to queue multiple maps
        if not permission or True:
            for (q_fn, q_login, q_name) in self.map_queue:
                if q_login == login:
                    self.pyseco.send_chat_message("$i$fff> $f00You already "
                                       "queued a map. Drop it with $fff/drop "
                                       "$f00to queue a new map",
                                       login=login)
                    return

        response = self.pyseco.query((1, int(id_) - 1), "GetMapList")
        if isinstance(response, Fault):
            self.pyseco.send_chat_message("$i$fff> $f00Invalid map id.", login=login)
            return

        map_filename = response[0][0][0]["FileName"]
        map_name = response[0][0][0]["Name"]

        for (q_fn, q_login, q_name) in self.map_queue:
            if q_fm == map_filename:
                self.pyseco.send_chat_message("$i$fff> $f00Map already in queue.",
                                              login=login)
                return

        name = self.pyseco.get_player(login).get_nick_name()
        self.map_queue.append((map_filename, login, name))
        self.pyseco.send_chat_message("$i$fff> %sAdded map to queue: $z%s" %
                                      (self.chat_color, map_name))

    def drop_map(self, login):
        before = len(self.map_queue)
        self.map_queue = [x for x in self.map_queue if not x[1] == login]
        if len(self.map_queue) != before:
            self.pyseco.send_chat_message("$i$fff> %sDropped map(s) from queue."
                                          % self.chat_color,
                                          login=login)

    def restart(self, login):
        response = self.pyseco.query((), "GetCurrentMapInfo")
        map_filename = response[0][0]["FileName"]

        name = self.pyseco.get_player(login).get_nick_name()
        self.map_queue.appendleft((map_filename, login, name))

        self.pyseco.send_chat_message("$i$fff>> %sThe current map has been "
                "queued for restart by: $z$s%s" % (self.chat_color, name))

    def next(self, login):
        name = self.pyseco.get_player(login).get_nick_name()

        self.pyseco.query((), "NextMap")
        self.pyseco.send_chat_message("$i$fff>> %sThe current map has been "
                "skipped by: $z$s%s" % (self.chat_color, name))

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
        elif command == "remove" and (admin or mod):
            if len(params) == 0:
                self.remove_current()
        elif command == "queue":
            if len(params) == 1:
                self.queue_map(params[0], login, (admin or mod))
        elif command == "drop":
            if len(params) == 0:
                self.drop_map(login)
        elif command == "restart" and (admin or mod):
            if len(params) == 0:
                self.restart(login)
        elif command == "next" and (admin or mod):
            if len(params) == 0:
                self.next(login)
