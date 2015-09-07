import pymysql
import warnings
import codecs

class DBException(Exception):
    def __init__(self):
        Exception.__init__(self)

    def __init__(self, msg):
        Exception.__init__(self, msg)

class PySECO_DB():
    def __init__(self, host, username, password, db):
        try:
            self.conn = pymysql.connect(host = host, user = username, password = password, db = db)
            self.cursor = self.conn.cursor()
            self.setup()
        except pymysql.err.OperationalError:
            raise DBException("connection failed")
        except Exception as e:
            raise e

    def setup(self):
        with warnings.catch_warnings():
            warnings.filterwarnings("error")
            try:
                self.cursor.execute("CREATE TABLE IF NOT EXISTS player (id INT UNSIGNED NOT NULL AUTO_INCREMENT, login VARCHAR(64) NOT NULL, nickname VARCHAR(128) NOT NULL, PRIMARY KEY(id), UNIQUE KEY(login))")
            except pymysql.err.Warning as e:
                pass
            try:
                self.cursor.execute("CREATE TABLE IF NOT EXISTS map (id INT UNSIGNED NOT NULL AUTO_INCREMENT, uid VARCHAR(64) NOT NULL, name VARCHAR(128) NOT NULL, author VARCHAR(64) NOT NULL, num_cp SMALLINT NOT NULL, authortime INT NOT NULL, PRIMARY KEY(id), UNIQUE KEY(uid))")
            except pymysql.err.Warning as e:
                pass
            try:
                self.cursor.execute("""CREATE TABLE IF NOT EXISTS record (pid INT UNSIGNED NOT NULL, mid INT UNSIGNED NOT NULL, time INT UNSIGNED NOT NULL, timestamp BIGINT UNSIGNED NOT NULL, PRIMARY KEY(pid,mid),
                    CONSTRAINT fk_playerRecord FOREIGN KEY (pid) REFERENCES player(id) ON UPDATE CASCADE ON DELETE CASCADE,
                    CONSTRAINT fk_mapRecord FOREIGN KEY (mid) REFERENCES map(id) ON UPDATE CASCADE ON DELETE CASCADE)""")
            except pymysql.err.Warning as e:
                pass
            self.conn.commit()

    def close(self):
        self.conn.commit()
        self.conn.close()

    def add_player(self, login, nickname):
        try:
            self.cursor.execute("INSERT INTO player (login,nickname) VALUES (%s,%s)",(login, nickname))
        except pymysql.MySQLError as e:
            pass
        self.conn.commit()
        self.cursor.execute("SELECT id FROM player WHERE login = %s LIMIT 1",(login))

        data = self.cursor.fetchone()
        if data is None:
            raise DBException("Failed to create/load player")

        return(data[0])

    def add_map(self, uid, name, author, num_cp, authortime):
        try:
            self.cursor.execute("INSERT INTO map (uid,name,author,num_cp,authortime) VALUES (%s,%s,%s,%s,%s)",(uid,name,author,num_cp,authortime))
        except pymysql.MySQLError as e:
            pass
        try:
            self.conn.commit()
        except pymysql.err.IntegrityError:
            pass
        self.cursor.execute("SELECT id FROM map WHERE uid = %s LIMIT 1",(uid))

        data = self.cursor.fetchone()
        if data is None:
            raise DBException("Failed to create/load map")

        return(data[0])

    def get_record(self, mid, pid):
        self.conn.commit()
        self.cursor.execute("SELECT time FROM record WHERE pid = %s AND mid = %s LIMIT 1" , (pid,mid))
        data = self.cursor.fetchone()

        if data is None:
            return None
        else:
            return data[0]

    def get_record_list(self, mid, login):
        self.conn.commit()
        # Params:
        # Map ID, Map ID, Map ID, Player Login, Map ID, Map ID, Map ID
        self.cursor.execute("""(SELECT (@row_number := @row_number + 1) AS rank,
            top.* FROM (SELECT record.time, player.login, player.nickname
            FROM record,
                player
            WHERE record.pid = player.id
                AND record.mid = %s
            ORDER BY record.time, record.timestamp ASC
            LIMIT 3) top,
            (SELECT @row_number := 0) r)
        UNION
        (SELECT new.* FROM
            (SELECT (@row_number:=@row_number + 1) AS rank,
                record.time, player.login, player.nickname
            FROM record,
                (SELECT @row_number := 0) r,
                player
            WHERE record.mid = %s
                AND  record.pid = player.id
            ORDER BY record.time, record.timestamp ASC
            LIMIT 200) new,
            (SELECT COUNT(*) as count, target_rank FROM
                (SELECT (@row_number:=@row_number + 1) AS target_rank,
                    record.mid, record.pid, record.time, record.timestamp
                FROM record,
                    (SELECT @row_number := 0) r
                WHERE record.mid = %s
                ORDER BY record.time, record.timestamp ASC
                LIMIT 200) t,
                player
            WHERE player.id = t.pid
                AND player.login = %s) x
        WHERE (x.count = 1 AND rank >= LEAST(GREATEST(4,(SELECT COUNT(*) FROM record WHERE record.mid = %s)-10),200-10,GREATEST(x.target_rank-5 , 4)) AND rank <= LEAST(GREATEST(4,(SELECT COUNT(*) FROM record WHERE record.mid = %s)),200,GREATEST(x.target_rank-5,4)+10))
            OR (x.count != 1 AND rank >= GREATEST(4,LEAST(200,(SELECT COUNT(*) FROM record WHERE record.mid = %s))-9)));""", (mid, mid, mid, login, mid, mid, mid))
        data = self.cursor.fetchall()
        out = []

        for element in data:
            out.append(element[:3] + (element[3].encode().decode("unicode_escape"),))


        return out

    # returns 0 if new record was created
    # returns previous record else
    def handle_record(self,mid,login,time,timestamp):
        self.conn.commit()
        retval = -1

        self.cursor.execute("SELECT time,id FROM record,player WHERE mid = %s AND pid = player.id and login = %s LIMIT 1", (mid,login))
        data = self.cursor.fetchone()
        if data is None:
            self.cursor.execute("INSERT INTO record (mid,pid,time,timestamp) VALUES (%s,(SELECT id FROM player WHERE login = %s LIMIT 1),%s,%s)",(mid,login,time,timestamp))
            retval = 0
        else:
            if time < data[0]:
                self.cursor.execute("UPDATE record SET time = %s, timestamp = %s WHERE mid = %s AND pid = (SELECT id FROM player WHERE login = %s LIMIT 1) LIMIT 1",(time,timestamp,mid,login))
                retval = data[0]
            else:
                retval = time
        self.conn.commit()
        return retval
