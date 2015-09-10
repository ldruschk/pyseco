from plugins.pyseco_plugin import pyseco_plugin


class manialink(pyseco_plugin):
    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco)
        self.pyseco.add_callback_listener("TrackMania.BeginChallenge", self)
        self.pyseco.add_callback_listener("TrackMania.EndRound", self)

        self.pyseco.query((), "SendHideManialinkPage")

    def process_callback(self, value):
        if value[1] == "TrackMania.BeginChallenge":
            self.overwrite_manialinks(ingame=False)
        elif value[1] == "TrackMania.EndRound":
            self.overwrite_manialinks(ingame=True)

    def overwrite_manialinks(self, ingame=True):
        mls = self.pyseco.get_manialinks(ingame)

        for id_ in mls:
            xml = "<manialink id='%s'/>" % id_
            self.pyseco.send((xml, 0, False), "SendDisplayManialinkPage")

        self.pyseco.reset_manialinks(ingame)
