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
                self.cursor.execute("""CREATE TABLE IF NOT EXISTS record (id INT UNSIGNED NOT NULL AUTO_INCREMENT, pid INT UNSIGNED NOT NULL, mid INT UNSIGNED NOT NULL,PRIMARY KEY(id), UNIQUE(pid,mid),
                    CONSTRAINT fk_playerRecord FOREIGN KEY (pid) REFERENCES player(id) ON UPDATE CASCADE ON DELETE CASCADE,
                    CONSTRAINT fk_mapRecord FOREIGN KEY (mid) REFERENCES map(id) ON UPDATE CASCADE ON DELETE CASCADE)""")
            except pymysql.err.Warning as e:
                pass
            self.conn.commit()

    def player_add(self, login, nickname):
        try:
            self.cursor.execute("INSERT INTO player (login,nickname) VALUES (%s,%s)",(login, nickname))
            self.conn.commit()
            self.cursor.execute("SELECT id FROM users WHERE login = %s",(login))

            data = self.cursor.fetchone()
            if data is None:
                raise DBException("Failed to create/load player")

            return(data[0])
        except pymysql.MySQLError as e:
            raise DBException("Failed to create/load player")
