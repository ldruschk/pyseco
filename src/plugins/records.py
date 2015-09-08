import time

from db import DBException
from plugins.pyseco_plugin import pyseco_plugin


class records(pyseco_plugin):
    claimed_msg = "$fff$i>> %sPlayer $z$s%s$z$s$i%s claimed the $aaa%d%s. record with: $fff%d"
    improved_msg = "$fff$i>> %sPlayer $z$s%s$z$s$i%s improved his $aaa%d%s. record with: $fff%d%s (-$fff%d%s)"
    equaled_msg = "$fff$i>> %sPlayer $z$s%s$z$s$i%s equaled his $aaa%d%s. record with: $fff%d"
    gained_msg = "$fff$i>> %sPlayer $z$s%s$z$s$i%s gained the $aaa%d%s. record with: $fff%d%s (-$aaa%d%s, -$fff%d%s)"

    def gen_claimed_msg(self, nick_name, prev_rank, prev_time,
                                          new_rank, new_time):
        return self.claimed_msg % (
                self.pyseco.chat_color,
                nick_name,
                self.pyseco.chat_color,
                new_rank,
                self.pyseco.chat_color,
                new_time)

    def gen_improved_msg(self, nick_name, prev_rank, prev_time,
                                          new_rank, new_time):
        return self.improved_msg % (
            self.pyseco.chat_color,
            nick_name,
            self.pyseco.chat_color,
            new_rank,
            self.pyseco.chat_color,
            new_time,
            self.pyseco.chat_color,
            prev_time-new_time,
            self.pyseco.chat_color)

    def gen_equaled_msg(self, nick_name, prev_rank, prev_time,
                                          new_rank, new_time):
        return self.equaled_msg % (
            self.pyseco.chat_color,
            nick_name,
            self.pyseco.chat_color,
            new_rank,
            self.pyseco.chat_color,
            new_time)

    def gen_gained_msg(self, nick_name, prev_rank, prev_time,
                                          new_rank, new_time):
        return self.gained_msg % (
            self.pyseco.chat_color,
            nick_name,
            self.pyseco.chat_color,
            new_rank,
            self.pyseco.chat_color,
            new_time,
            self.pyseco.chat_color,
            prev_rank-new_rank,
            self.pyseco.chat_color,
            prev_time-new_time,
            self.pyseco.chat_color)

    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco, db=True)
        self.initialize()

        self.pyseco.add_callback_listener("TrackMania.PlayerFinish", self)
        self.pyseco.add_callback_listener("TrackMania.PlayerConnect", self)
        self.pyseco.add_callback_listener("TrackMania.BeginChallenge", self)
        self.pyseco.add_callback_listener("TrackMania.EndRound", self)

    def initialize(self):
        challenge = self.pyseco.query((), "GetCurrentMapInfo")
        self.new_map(challenge[0][0])

    def process_callback(self, value):
        if value[1] == "TrackMania.PlayerFinish":
            self.db.get_record_list(self.map_id, value[0][1])
            # Player only restarted, ignore
            if value[0][2] == 0:
                return
            ranking = self.pyseco.query((value[0][1], ),
                                        "GetCurrentRankingForLogin")
            self.process_finish(value[0][2], ranking[0][0][0])
        if value[1] == "TrackMania.BeginChallenge":
            self.new_map(value[0][0])

    def process_finish(self, newtime, ranking):
        login = ranking["Login"]
        player = self.pyseco.get_player(login)
        nick_name = player.get_nick_name()
        rec_time = ranking["BestTime"]
        if newtime > rec_time:
            return
        (prev_rank, prev_time, new_rank, new_time) = self.db.handle_record(
                                                     self.map_id, login,
                                                     rec_time, int(time.time()))
        tuple_ = (prev_rank, prev_time, new_rank, new_time)

        # new time is worse than the record in the db
        if prev_time is not None and newtime > prev_time:
            return


        # player claimed a record
        if prev_rank is None and new_rank is not None:
            self.pyseco.send_chat_message(self.gen_claimed_msg(nick_name,*tuple_))
        # player has the same rank as before
        elif prev_rank is not None and prev_rank == new_rank:
            # player improved his time but kept his rank
            if new_time < prev_time:
                self.pyseco.send_chat_message(self.gen_improved_msg(nick_name,*tuple_))
            # player equaled his record
            elif new_time == prev_time:
                self.pyseco.send_chat_message(self.gen_equaled_msg(nick_name,*tuple_))
        # player gained a record
        elif prev_rank is not None and new_rank < prev_rank:
            self.pyseco.send_chat_message(self.gen_gained_msg(nick_name,*tuple_))


    def new_map(self, value):
        try:
            self.map_id = self.db.add_map(value["UId"],
                                          value["Name"],
                                          value["Author"],
                                          value["NbCheckpoints"],
                                          value["AuthorTime"])
        except DBException as e:
            self.error_log(str(e), fatal=True)
