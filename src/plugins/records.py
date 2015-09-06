from plugins.pyseco_plugin import pyseco_plugin

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
            if value[0][2] == 0: # Player only restarted, ignore
                return
            ranking = self.pyseco.query((value[0][1],),"GetCurrentRankingForLogin")
            self.process_finish(ranking[0][0][0])
        if value[1] == "TrackMania.BeginChallenge":
            self.new_map(value[0][0])

    def add_player(self, login, player = None):
        if not player:
            player = self.pyseco.get_player(login)
        if not player:
            return
        record = self.pyseco.db.get_record(self.map_id, player.db_id)
        if record:
            self.records[login] = record

    def process_finish(self, ranking):
        login = ranking["Login"]
        player = self.pyseco.get_player(login)
        time = ranking["BestTime"]
        if login not in self.records: # Make sure that the player does not have a record yet
            self.add_player(login)
        if login not in self.records:
            self.pyseco.db.add_record(self.map_id,player.db_id,time)
            self.add_player(login)
        elif time < self.records[login]:
            self.pyseco.db.update_record(self.map_id,player.db_id,time)

    def new_map(self, value):
        self.map_id = self.pyseco.db.add_map(value["UId"],value["Name"],value["Author"],value["NbCheckpoints"],value["AuthorTime"])
        self.records = dict()
        for login, player in self.pyseco.players.items():
            self.add_player(login,player)
