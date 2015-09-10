from plugins.pyseco_plugin import pyseco_plugin
import time
from threading import Thread


class mapinfo(pyseco_plugin):
    info_manialink = """<manialink id='%s'>
    <frame posn='%f %f %f'>
        <quad sizen='%f %f' style='%s' substyle='%s'/>
        <label posn='%f %f %f' sizen='%f %f' textsize='%f' text='%s'/>
        <label posn='%f %f %f' sizen='%f %f' textsize='%f' text='%s'/>
        <label posn='%f %f %f' sizen='%f %f' textsize='%f' text='%s'/>
    </frame>
</manialink>"""

    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco)
        self.register_callback("TrackMania.BeginChallenge")
        self.register_callback("TrackMania.EndChallenge")
        self.register_callback("TrackMania.StatusChanged")

        self.initialize()

    def initialize(self):
        response = self.pyseco.query((), "GetCurrentMapInfo")
        self.show_current_info(response[0][0])

    def process_callback(self, value):
        if value[1] == "TrackMania.BeginChallenge":
            response = self.pyseco.query((), "GetCurrentMapInfo")
            self.show_current_info(response[0][0])


    def show_current_info(self, info):
        name = info["Name"].replace("'","&apos;")
        author = info["Author"].replace("'","&apos;")
        time = info["AuthorTime"]
        timestr = "%d.%03d" % (int(time/1000), time%1000)

        xml = self.info_manialink % ("mapinfo",
            48.75, 47.75, 0,
            15, 7, "BgsPlayerCard", "BgCard",
            1, -1, 0, 13, 2, 2, name,
            1, -3.25, 0, 13, 1, 1, author,
            1, -5, 0, 13, 1, 1, timestr
        )
        response = self.pyseco.query((xml, 0, False), "SendDisplayManialinkPage")
        print(response)

        self.pyseco.send_chat_message(str(info))
