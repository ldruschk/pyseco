import time
import threading

from db import DBException
from plugins.pyseco_plugin import pyseco_plugin
from xmlrpc.client import Fault


class recordsgui(pyseco_plugin):
    # str: id
    # frame(float x,y,z)
    # quad(float width,height)
    # header(frame(x,y,z), label(x,y,z,width,height), textsize, text)
    # str: entries (as xml)
    local_records_xml = """<manialink id='%s'>
        <frame posn='%f %f %f' halign='left' valign='top'>
            <quad posn='%f %f %f' sizen='%f %f' style='%s' substyle='%s' />
            <quad posn='%f %f %f' sizen='%f %f' style='%s' substyle='%s' />
            <frame posn='%f %f %f'>
                <label posn='%f %f %f' sizen='%f %f' textsize='%f' text='%s' />
            </frame>
            %s
        </frame>
    </manialink>"""

    # frame(float x,y,z)
    # 3xlabel(float x,y,z, width, height, textsize | str: text)
    local_records_entry_xml = """<frame posn='%f %f %f'>
        <label posn='%f %f %f' sizen='%f %f' textsize='%f' text='%s' />
        <label posn='%f %f %f' sizen='%f %f' textsize='%f' text='%s' />
        <label posn='%f %f %f' sizen='%f %f' textsize='%f' text='%s' />
    </frame>"""

    live_records_xml = """<manialink id='%s'>
        <frame posn='%f %f %f' halign='left' valign='top'>
            <quad posn='%f %f %f' sizen='%f %f' style='%s' substyle='%s' />
            <quad posn='%f %f %f' sizen='%f %f' style='%s' substyle='%s' />
            <frame posn='%f %f %f'>
                <label posn='%f %f %f' sizen='%f %f' textsize='%f' text='%s' />
            </frame>
            %s
        </frame>
    </manialink>"""

    live_records_entry_xml = """<frame posn='%f %f %f'>
        <label posn='%f %f %f' sizen='%f %f' textsize='%f' text='%s' />
        <label posn='%f %f %f' sizen='%f %f' textsize='%f' text='%s' />
        <label posn='%f %f %f' sizen='%f %f' textsize='%f' text='%s' />
    </frame>"""

    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco, db=True)
        self.pyseco.add_callback_listener("TrackMania.BeginRound", self)
        self.pyseco.add_callback_listener("TrackMania.EndRound", self)
        self.pyseco.add_callback_listener("TrackMania.BeginChallenge", self)

        self.update_event = threading.Event()

        self.initialize()

    def initialize(self):
        challenge = self.pyseco.query((), "GetCurrentMapInfo")
        self.new_map(challenge[0][0])
        status = self.pyseco.query((), "GetStatus")
        self.update = status[0][0]["Code"] == 4 # Challenge running

        self.update_thread = threading.Thread(target=self.handle_updates,
                                              args=(2, ),
                                              daemon=True)
        self.update_thread.start()

    def process_callback(self, value):
        if value[1] == "TrackMania.EndRound":
            self.update = False
        elif value[1] == "TrackMania.BeginRound":
            self.update = True
        elif value[1] == "TrackMania.BeginChallenge":
            self.new_map(value[0][0])
            self.update = True

    def handle_updates(self, refresh):
        last_update = -1
        while True:
            while (not self.update_event.is_set()) and (not self.update or int(time.time()) < last_update + refresh):
                time.sleep(1)
            if self.update_event.is_set():
                break
            self.update_locals()
            self.update_live()
            last_update = int(time.time())

    def update_locals(self):
        for login, player in self.pyseco.players.items():
            ranking = self.db.get_record_list(self.map_id, login)
            xml = self.gen_local_xml(login,
                                     player.get_nick_name(),
                                     ranking)
            self.pyseco.send((login, xml, 0, False),
                             "SendDisplayManialinkPageToLogin")
        self.pyseco.add_manialink("local_records",ingame=True)

    def update_live(self):
        ranking = self.pyseco.query((200, 0), "GetCurrentRanking")
        if isinstance(ranking, Fault):
            return

        rank_list = []
        for rank in ranking[0][0]:
            if rank["Rank"] == 0:
                continue
            tup = (rank["Rank"], rank["BestTime"], rank["Login"], rank["NickName"])
            rank_list.append(tup)
        rank_list.sort(key=lambda tup: tup[0])

        for login, player in self.pyseco.players.items():
            xml = self.gen_live_xml(login, player.get_nick_name(),
                                    rank_list)
            self.pyseco.send((login, xml, 0, False),
                             "SendDisplayManialinkPageToLogin")
        self.pyseco.add_manialink("live_records",ingame=True)

    def stop(self):
        self.update_event.set()
        pyseco_plugin.stop(self)

    def new_map(self, value):
        try:
            self.map_id = self.db.add_map(value["UId"],
                                          value["Name"],
                                          value["Author"],
                                          value["NbCheckpoints"],
                                          value["AuthorTime"])
        except DBException as e:
            self.error_log(str(e), fatal=True)

    def gen_live_xml(self, player_login, player_name, rec_list):
        entry_xml = ""
        i = 0

        try:
            rec_index = [x[2] for x in rec_list].index(player_login)
        # Player has no live record
        except ValueError:
            rec_index = -1

        new_list = []
        if rec_index >= 0 and rec_index <= 2:
            new_list = rec_list[:14]
        else:
            if rec_index == -1:
                new_list = rec_list[:3]
                start_index = max(len(rec_list) - 10, 3)
                new_list += rec_list[start_index:]
            else:
                new_list = rec_list[:3]
                start_index = max(3, min(rec_index - 5, len(rec_list)-11))
                end_index = start_index + 11
                new_list += rec_list[start_index:end_index]

        has_rec = rec_index != -1

        for entry in new_list:
            rank = entry[0]
            time = entry[1]
            login = entry[2]
            name = entry[3]

            color = "$s$fff"
            if player_login == login:
                color = "$s$f08"
            elif rank <= 3:
                color = "$s$bbb"
            rank_str = "%s%d." % (color, rank)
            time_str = "%s%d.%03d" % (color, int(time/1000), time % 1000)

            entry_xml += self.live_records_entry_xml % (0.5, -2.5-i*1.5, 0,
                         0, 0, 0, 1.5, 1, 1, rank_str,
                         2, 0, 0, 3, 1, 1, time_str,
                         5.5, 0, 0, 7, 1, 1, name.replace("'", "&apos;"))

            i += 1
        if not has_rec:
            entry_xml += self.live_records_entry_xml % (0.5, -2.5-i*1.5, 0,
                        0, 0, 0, 1.5, 1, 1, "$f08--.",
                        2, 0, 0, 3, 1, 1, "$f08--.---",
                        5.5, 0, 0, 7, 1, 1, player_name.replace("'", "&apos;"))

        return self.live_records_xml % ("live_records",
                50.25, 7.5, 0,
                0, 0, 0, 13.5, 24, "BgsPlayerCard", "BgCard",
                0.25, -0.25, 1, 13, 2, "BgRaceScore2", "BgScores",
                0.5, -0.5, 0,
                0, 0, 2, 12.5, 1, 1, "$fff$s$iLive Records:", entry_xml)

    def gen_local_xml(self, player_login, player_name, rec_list):
        entry_xml = ""
        i = 0
        has_rec = False
        for entry in rec_list:
            rank = entry[0]
            time = entry[1]
            login = entry[2]
            name = entry[3]

            color = "$s$fff"
            if player_login == login:
                color = "$s$f08"
                has_rec = True
            elif rank <= 3:
                color = "$s$bbb"
            rank_str = "%s%d." % (color, rank)
            time_str = "%s%d.%03d" % (color, int(time/1000), time % 1000)

            entry_xml += self.local_records_entry_xml % (0.5, -2.5-i*1.5, 0,
                         0, 0, 0, 1.5, 1, 1, rank_str,
                         2, 0, 0, 3, 1, 1, time_str,
                         5.5, 0, 0, 7, 1, 1, name.replace("'", "&apos;"))
            i += 1
        if not has_rec:
            entry_xml += self.local_records_entry_xml % (0.5, -2.5-i*1.5, 0,
                        0, 0, 0, 1.5, 1, 1, "$f08--.",
                        2, 0, 0, 3, 1, 1, "$f08--.---",
                        5.5, 0, 0, 7, 1, 1, player_name.replace("'", "&apos;"))

        return self.local_records_xml % ("local_records",
                50.25, 32, 0,
                0, 0, 0, 13.5, 24, "BgsPlayerCard", "BgCard",
                0.25, -0.25, 1, 13, 2, "BgRaceScore2", "BgScores",
                0.5, -0.5, 0,
                0, 0, 2, 12.5, 1, 1, "$fff$i$sLocal Records:", entry_xml)
