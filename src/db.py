import pymysql
import warnings

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
                self.cursor.execute("CREATE TABLE IF NOT EXISTS player (id INT UNSIGNED NOT NULL AUTO_INCREMENT, login VARCHAR(64) NOT NULL, nickname VARCHAR(128) NOT NULL, PRIMARY KEY(id), UNIQUE(login))")
            except pymysql.err.Warning as e:
                pass
            try:
                self.cursor.execute("CREATE TABLE IF NOT EXISTS map (id INT UNSIGNED NOT NULL AUTO_INCREMENT, uid VARCHAR(64) NOT NULL, name VARCHAR(128) NOT NULL, author VARCHAR(64) NOT NULL, num_cp SMALLINT NOT NULL, authortime INT NOT NULL, PRIMARY KEY(id), UNIQUE(uid))")
            except pymysql.err.Warning as e:
                pass
            try:
                self.cursor.execute("""CREATE TABLE IF NOT EXISTS record (pid INT UNSIGNED NOT NULL, mid INT UNSIGNED NOT NULL, time INT UNSIGNED NOT NULL, PRIMARY KEY(pid,mid),
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
        self.conn.commit()
        self.cursor.execute("SELECT id FROM map WHERE uid = %s LIMIT 1",(uid))

        data = self.cursor.fetchone()
        if data is None:
            raise DBException("Failed to create/load map")

        return(data[0])

    def get_record(self, mid, pid):
        self.cursor.execute("SELECT time FROM record WHERE pid = %s AND mid = %s LIMIT 1" , (pid,mid))
        data = self.cursor.fetchone()

        if data is None:
            return None
        else:
            return data[0]

    def add_record(self, mid, pid, time):
        try:
            self.cursor.execute("INSERT INTO record (mid,pid,time) VALUES (%s,%s,%s)",(mid,pid,time))
            self.conn.commit()
        except pymysql.MySQLError as e:
            raise DBException("Could not create record for %d on %d" % (pid,mid))

    def update_record(self, mid, pid, time):
        try:
            self.cursor.execute("UPDATE record SET time = %s WHERE mid = %s AND pid = %s",(time,mid,pid))
            self.conn.commit()
        except pymysql.MySQLError as e:
            raise DBException("Could not update record for %d on %d" % (pid,mid))
