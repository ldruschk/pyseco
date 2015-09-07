from plugins.pyseco_plugin import pyseco_plugin
import time

class records(pyseco_plugin):
    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco)
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
            self.pyseco.db.get_record_list(self.map_id, value[0][1])
            if value[0][2] == 0: # Player only restarted, ignore
                return
            ranking = self.pyseco.query((value[0][1],),"GetCurrentRankingForLogin")
            self.process_finish(value[0][2],ranking[0][0][0])
        if value[1] == "TrackMania.BeginChallenge":
            self.new_map(value[0][0])

    '''def add_player(self, login, player = None):
        if not player:
            player = self.pyseco.get_player(login)
        if not player:
            return
        record = self.pyseco.db.get_record(self.map_id, player.db_id)
        if record:
            self.records[login] = record'''

    def process_finish(self, newtime,ranking):
        print(newtime,ranking)
        login = ranking["Login"]
        player = self.pyseco.get_player(login)
        rec_time = ranking["BestTime"]
        if newtime > rec_time:
            return
        prev = self.pyseco.db.handle_record(self.map_id, login, rec_time, int(time.time()))
        if prev == 0:
            self.pyseco.send_chat_message("Player %s claimed record with: %d" % (player.get_nick_name(), rec_time))
        elif rec_time < prev:
            self.pyseco.send_chat_message("Player %s improved record with: %d (-%d)" % (player.get_nick_name(), rec_time, prev-rec_time))
        elif rec_time == prev:
            self.pyseco.send_chat_message("Player %s equaled his record with: %d" % (player.get_nick_name(), prev))

    def new_map(self, value):
        self.map_id = self.pyseco.db.add_map(value["UId"],value["Name"],value["Author"],value["NbCheckpoints"],value["AuthorTime"])
        #self.records = dict()
        #for login, player in self.pyseco.players.items():
            #self.add_player(login,player)
