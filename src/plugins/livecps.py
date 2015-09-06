from plugins.pyseco_plugin import pyseco_plugin

class livecps(pyseco_plugin):
    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco)
        self.pyseco.add_callback_listener("TrackMania.PlayerCheckpoint", self)

    def process_callback(self, value):
        if value[1] == "TrackMania.PlayerCheckpoint":
            self.process_checkpoint(value[0])

    def process_checkpoint(self, value):
        self.pyseco.send_chat_message("Player %s achieved time %d on cp #%d" % (value[1], value[2], value[4]))
