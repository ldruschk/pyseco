from plugins.pyseco_plugin import pyseco_plugin
import time
from db import DBException

class records(pyseco_plugin):
    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco, db = True)
        self.initialize()

        self.pyseco.add_callback_listener("TrackMania.PlayerFinish",self)
        self.pyseco.add_callback_listener("TrackMania.PlayerConnect",self)
        self.pyseco.add_callback_listener("TrackMania.BeginChallenge",self)
        self.pyseco.add_callback_listener("TrackMania.EndRound",self)

    def initialize(self):
        challenge = self.pyseco.query((),"GetCurrentMapInfo")
        self.new_map(challenge[0][0])

    def process_callback(self, value):
        if value[1] == "TrackMania.PlayerFinish":
            self.db.get_record_list(self.map_id, value[0][1])
            if value[0][2] == 0: # Player only restarted, ignore
                return
            ranking = self.pyseco.query((value[0][1],),"GetCurrentRankingForLogin")
            self.process_finish(value[0][2],ranking[0][0][0])
        if value[1] == "TrackMania.BeginChallenge":
            self.new_map(value[0][0])

    def process_finish(self, newtime,ranking):
        login = ranking["Login"]
        player = self.pyseco.get_player(login)
        rec_time = ranking["BestTime"]
        if newtime > rec_time:
            return
        prev = self.db.handle_record(self.map_id, login, rec_time, int(time.time()))
        if prev == 0:
            self.pyseco.send_chat_message("Player %s claimed record with: %d" % (player.get_nick_name(), rec_time))
        elif rec_time < prev:
            self.pyseco.send_chat_message("Player %s improved record with: %d (-%d)" % (player.get_nick_name(), rec_time, prev-rec_time))
        elif rec_time == prev:
            self.pyseco.send_chat_message("Player %s equaled his record with: %d" % (player.get_nick_name(), prev))

    def new_map(self, value):
        try:
            self.map_id = self.db.add_map(value["UId"],value["Name"],value["Author"],value["NbCheckpoints"],value["AuthorTime"])
        except DBException as e:
            self.error_log(str(e),fatal = True)
