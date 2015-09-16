from plugins.pyseco_plugin import pyseco_plugin
from db import DBException


class cpdiff(pyseco_plugin):
    cpdiff_manialink = """<manialink id='cpdiff'>
        <frame posn="%f %f %f">
            <quad sizen='%f %f' style='%s' substyle='%s'/>
            <label posn='%f %f %f' sizen='%f %f' textsize='%f' text='%s'/>
            <label posn='%f %f %f' sizen='%f %f' textsize='%f' text='%s'
                halign='right'/>
        </frame>
    </manialink>"""

    def format_manialink(self, cp_num, cp_text):
        return self.cpdiff_manialink % (
            -6, -39, 0,
            12, 3, "BgsPlayerCard", "BgCard",
            1, -0.5, 0, 2.5, 2, 2, "$s$aaaCP%d:" % int(cp_num + 1),
            11, -0.5, 0, 7.5, 2, 2, cp_text
        )

    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco, db=True)
        self.register_callback("TrackMania.BeginChallenge")
        self.register_callback("TrackMania.PlayerCheckpoint")
        self.register_callback("TrackMania.PlayerFinish")

        self.curr_times = dict()

        challenge = self.pyseco.query((), "GetCurrentMapInfo")
        self.new_map(challenge[0][0])

    def process_callback(self, value):
        if value[1] == "TrackMania.BeginChallenge":
            self.new_map(value[0][0])
            self.curr_times = dict()
        elif value[1] == "TrackMania.PlayerCheckpoint":
            self.handle_checkpoint(value[0])
        elif value[1] == "TrackMania.PlayerFinish":
            if value[0][2] == 0:
                self.show_manialink(value[0][1], -1, "$s$aaa-.---")
            else:
                # remove the saved checkpoint times so they will be fetched
                # again next time, to make sure the new times are loaded if a
                # player got a new record
                del self.curr_times[value[0][1]]

    def handle_checkpoint(self, value):
        login = value[1]
        cp_time = value[2]
        cp_num = value[4]

        if login not in self.curr_times:
            self.load_times(login)

        cp_text = ""

        if cp_num not in self.curr_times[login]:
            cp_text = "$s$aaa-.---"
        else:
            diff = cp_time - self.curr_times[login][cp_num]
            if diff > 0:
                cp_text = "$s$f00+%s" % self.format_time(diff)
            else:
                cp_text = "$s$00f-%s" % self.format_time(-diff)

        self.show_manialink(login, cp_num, cp_text)

    def show_manialink(self, login, cp_num, cp_text):
        xml = self.format_manialink(cp_num, cp_text)
        self.pyseco.add_manialink("cpdiff", ingame=True)

        self.pyseco.send((login, xml, 0, False),
                         "SendDisplayManialinkPageToLogin")

    def format_time(self, time):
        return "%d.%03d" % (int(time/1000), time % 1000)

    def load_times(self, login):
        out_dict = dict()
        data = self.db.get_cp_times(self.map_id, login)
        rec = self.db.get_record_by_login(self.map_id, login)
        for (num, time) in data:
            out_dict[num] = time
        if rec is not None:
            out_dict[self.nb_checkpoints - 1] = rec

        self.curr_times[login] = out_dict

    def new_map(self, value):
        try:
            self.map_id = self.db.add_map(value["UId"],
                                          value["Name"],
                                          value["Author"],
                                          value["NbCheckpoints"],
                                          value["AuthorTime"])
            self.nb_checkpoints = value["NbCheckpoints"]
        except DBException as e:
            self.error_log(str(e), fatal=True)
