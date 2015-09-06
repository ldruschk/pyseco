from plugins.pyseco_plugin import pyseco_plugin
from pyseco import Player

class playermanager(pyseco_plugin):
    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco)
        self.pyseco.add_callback_listener("TrackMania.PlayerConnect", self)
        self.pyseco.add_callback_listener("TrackMania.PlayerDisonnect", self)
        self.pyseco.add_callback_listener("TrackMania.PlayerInfoChanged", self)
        self.initialize()

    def initialize(self):
        player_list = self.pyseco.query((300,0),"GetPlayerList")
        for player in player_list[0][0]:
            self.player_add(player)

    def process_callback(self, value):
        if value[1] == "TrackMania.PlayerConnect":
            player_info = self.pyseco.query((value[0][0],),"GetPlayerInfo")
            self.player_add(player_info[0][0])
        if value[1] == "TracMania.PlayerDisconnect":
            player_login = value[0][0]
            self.player_remove(player_login)
        if value[1] == "TrackMania.PlayerInfoChanged":
            player_info = self.pyseco.query((value[0][0]["Login"],),"GetPlayerInfo")
            self.player_modify(player_info[0][0])

    def player_add(self, player_info):
        if player_info["Login"] not in self.pyseco.players:
            self.pyseco.players[player_info["Login"]] = Player(player_info,self.pyseco)

    def player_modify(self, player_info):
        if player_info["Login"] in self.pyseco.players:
            self.pyseco.players[player_info["Login"]].modify(player_info)

    def player_remove(self, player_login):
        if player_login in self.pyseco.players:
            del self.pyseco.players[player_login]
