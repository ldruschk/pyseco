from plugins.pyseco_plugin import pyseco_plugin
import time
import threading

class recordsgui(pyseco_plugin):
    # str: id
    # frame(float x,y,z)
    # quad(float width,height)
    # header(frame(x,y,z), label(x,y,z,width,height), textsize, text)
    # str: entries (as xml)
    local_records_xml = """<manialink id='%s'>
    <frame posn='%f %f %f' halign='left' valign='top'>
        <quad sizen='%f %f' style='%s' substyle='%s' />
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

    def __init__(self, pyseco):
        pyseco_plugin.__init__(self, pyseco)
        self.pyseco.add_callback_listener("TrackMania.BeginRound",self)
        self.pyseco.add_callback_listener("TrackMania.EndRound",self)
        self.pyseco.add_callback_listener("TrackMania.BeginChallenge",self)

        self.initialize()

    def initialize(self):
        challenge = self.pyseco.query((),"GetCurrentMapInfo")
        self.new_map(challenge[0][0])
        status = self.pyseco.query((),"GetStatus")
        self.update = status[0][0]["Code"] == 4 # Challenge running

        self.update_thread = threading.Thread(target=self.handle_updates, args=(10,), daemon = True)
        self.update_thread.start()

    def process_callback(self, value):
        if value[1] == "TrackMania.EndRound":
            self.update = False
        elif value[1] == "TrackMania.BeginRound":
            self.update = True
        elif value[1] == "TrackMania.BeginChallenge":
            self.new_map(value[0][0])

    def handle_updates(self, refresh):
        last_update = -1
        while True:
            while not self.update or int(time.time()) < last_update + refresh:
                time.sleep(1)
            for login,player in self.pyseco.players.items():
                ranking = self.pyseco.db.get_record_list(self.map_id, login)
                xml = self.generate_local_xml(login,player.nick_name,ranking)
                self.pyseco.send((login,xml,0,False),"SendDisplayManialinkPageToLogin")
            last_update = int(time.time())

    def new_map(self, value):
        self.map_id = self.pyseco.db.add_map(value["UId"],value["Name"],value["Author"],value["NbCheckpoints"],value["AuthorTime"])

    def generate_local_xml(self, player_login, player_name, rec_list):
        entry_xml = ""
        i = 0
        has_rec = False
        for entry in rec_list:
            rank = entry[0]
            time = entry[1]
            login = entry[2]
            name = entry[3]

            color = "$fff"
            if player_login == login:
                color = "$f08"
                has_rec = True
            elif rank <= 3:
                color = "$bbb"
            rank_str = "%s%d." % (color, rank)
            time_str = "%s%d.%03d" % (color, int(time/1000), time % 1000)

            entry_xml += self.local_records_entry_xml % (0.5, -2-i*1.5, 0,
                0,0,0,1.5,1,1,rank_str,
                2,0,0,3,1,1,time_str,
                5.5,0,0,7,1,1,name.replace("'","&apos;"))
            i += 1
        if not has_rec:
            entry_xml += self.local_records_entry_xml % (0.5, -2-i*1.5,0,
                0,0,0,1.5,1,1,"$f08--.",
                2,0,0,3,1,1,"--.---",
                5.5,0,0,7,1,1,player_name.replace("'","&apos;"))

        return self.local_records_xml % ("local_records",50.25,32,0,13.5,23.5,"BgsPlayerCard","BgCard",
            0.5,-0.5,0,
            0,0,0,12.5,1,1,"$fff$oLocal Records:", entry_xml)
