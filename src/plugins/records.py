from plugins.pyseco_plugin import pyseco_plugin

class records(pyseco_plugin):
    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco)
        self.pyseco.add_callback_listener("TrackMania.PlayerFinish",self)
        self.pyseco.add_callback_listener("TrackMania.BeginRound",self)
        self.pyseco.add_callback_listener("TrackMania.EndRound",self)

    def process_callback(self, value):
        if value[1] == "TrackMania.PlayerFinish":
            if value[0][2] == 0: # Player only restarted, ignore
                return
            ranking = self.pyseco.query((value[0][1],),"GetCurrentRankingForLogin")
            print(ranking)
