from plugins.pyseco_plugin import pyseco_plugin

class manialink(pyseco_plugin):
    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco)
        self.pyseco.add_callback_listener("TrackMania.StatusChanged",self)
        self.pyseco.add_callback_listener("TrackMania.EndRound",self)

    def process_callback(self, value):
        if value[1] == "TrackMania.EndRound":
            self.pyseco.send((),"SendHideManialinkPage")
        elif value[1] == "TrackMania.StatusChanged":
            status = self.pyseco.query((),"GetStatus")
            if status[0][0]["Code"] != 4: # Challenge running
                self.pyseco.send((),"SendHideManialinkPage")
