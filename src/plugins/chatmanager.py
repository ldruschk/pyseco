from plugins.pyseco_plugin import pyseco_plugin
import shlex


class chatmanager(pyseco_plugin):
    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco, db=True)
        self.pyseco.add_callback_listener("TrackMania.PlayerChat", self)

    def process_callback(self, value):
        if value[1] == "TrackMania.PlayerChat":
            if value[0][3]:
                self.parse(value[0])

    def parse(self, value):
        user = value[1]
        # Todo: Check permissions

        out = shlex.split(value[2])
        command = out[0][1:]
        params = out[1:]

        self.pyseco.chat_command(command, params, user, admin=True, mod=True)
