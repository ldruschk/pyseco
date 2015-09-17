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
        %s
    </frame>
</manialink>"""
    next_str = "<label posn='%f %f %f' sizen='%f %f' textsize='%f' text='%s'/>"

    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco)
        self.register_callback("TrackMania.BeginChallenge")
        self.register_callback("pyseco.mapmanager.EndRound")
        self.register_callback("TrackMania.PlayerConnect")

        self.initialize()

    def initialize(self):
        response = self.pyseco.query((), "GetCurrentMapInfo")
        self.show_current_info(response[0][0])
        self.ingame = True

    def process_callback(self, value):
        if value[1] == "TrackMania.BeginChallenge":
            self.ingame = True
            response = self.pyseco.query((), "GetCurrentMapInfo")
            self.show_current_info(response[0][0])
        elif value[1] == "TrackMania.PlayerConnect":
            if self.ingame:
                response = self.pyseco.query((), "GetCurrentMapInfo")
                self.show_current_info(response[0][0], login=value[0][0])
            else:
                response = self.pyseco.query((), "GetNextMapInfo")
                self.show_current_info(response[0][0], login=value[0][0], next_=True)
        elif value[1] == "pyseco.mapmanager.EndRound":
            self.ingame = False
            response = self.pyseco.query((), "GetNextMapInfo")
            self.show_current_info(response[0][0], next_=True)


    def show_current_info(self, info, login=None, next_=False):
        name = info["Name"].replace("'","&apos;")
        author = info["Author"].replace("'","&apos;")
        time = info["AuthorTime"]
        timestr = "%d.%03d" % (int(time/1000), time%1000)

        next_str = ""
        if next_:
            next_str = self.next_str % (-6, -1, 0, 5, 1, 1, "$sNext Map:")

        xml = self.info_manialink % ("mapinfo",
            48.75, 47.75, 0,
            15, 7, "BgsPlayerCard", "BgCard",
            1, -1, 0, 13, 2, 2, name,
            1, -3.25, 0, 13, 1, 1, author,
            1, -5, 0, 13, 1, 1, timestr,
            next_str
        )
        if login is None:
            response = self.pyseco.query((xml, 0, False), "SendDisplayManialinkPage")
        else:
            response = self.pyseco.query((login, xml, 0, False), "SendDisplayManialinkPageToLogin")
