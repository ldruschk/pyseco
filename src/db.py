import pymysql
import warnings


class DBException(Exception):
    def __init__(self, msg=""):
        Exception.__init__(self, msg)


class PySECO_DB():
    def __init__(self, pyseco, host, username, password, db):
        self.pyseco = pyseco
        try:
            self.conn = pymysql.connect(
                host=host, user=username,
                password=password, db=db, autocommit=False)
            self.setup()
        except pymysql.err.OperationalError:
            raise DBException("connection failed")
        except Exception as e:
            raise e

    def setup(self):
        self.pyseco.db_lock.acquire()
        cur = self.conn.cursor()
        with warnings.catch_warnings():
            warnings.filterwarnings("error")
            try:
                cur.execute("""
                        CREATE TABLE IF NOT EXISTS player
                        (id INT UNSIGNED NOT NULL AUTO_INCREMENT,
                        login VARCHAR(64) NOT NULL,
                        nickname VARCHAR(128) NOT NULL,
                        PRIMARY KEY(id),
                        UNIQUE KEY(login))""")
            except pymysql.err.Warning as e:
                pass
            try:
                cur.execute("""
                        CREATE TABLE IF NOT EXISTS map
                        (id INT UNSIGNED NOT NULL AUTO_INCREMENT,
                        uid VARCHAR(64) NOT NULL,
                        name VARCHAR(128) NOT NULL,
                        author VARCHAR(64) NOT NULL,
                        num_cp SMALLINT NOT NULL,
                        authortime INT NOT NULL,
                        PRIMARY KEY(id),
                        UNIQUE KEY(uid))""")
            except pymysql.err.Warning as e:
                pass
            try:
                cur.execute("""
                        CREATE TABLE IF NOT EXISTS record
                        (pid INT UNSIGNED NOT NULL,
                        mid INT UNSIGNED NOT NULL,
                        time INT UNSIGNED NOT NULL,
                        timestamp BIGINT UNSIGNED NOT NULL,
                        PRIMARY KEY(pid,mid),
                        CONSTRAINT fk_playerRecord FOREIGN KEY (pid)
                            REFERENCES player(id)
                            ON UPDATE CASCADE ON DELETE CASCADE,
                        CONSTRAINT fk_mapRecord FOREIGN KEY (mid)
                            REFERENCES map(id)
                            ON UPDATE CASCADE ON DELETE CASCADE)""")
            except pymysql.err.Warning as e:
                pass
        cur.close()
        self.conn.commit()
        self.pyseco.db_lock.release()

    def close(self):
        try:
            self.conn.commit()
            self.conn.close()
        except Exception as e:
            pass

    def add_player(self, login, nickname):
        self.pyseco.db_lock.acquire()
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM player WHERE login = %s LIMIT 1", (login))
        data = cur.fetchone()
        if data is None:
            cur.execute(
                    "INSERT INTO player (login, nickname) VALUES (%s, %s)",
                    (login, nickname))
            cur.execute("SELECT last_insert_id()")
            data = cur.fetchone()
            if data is None:
                raise DBException("Failed to create/load player")
        cur.close()
        self.conn.commit()
        self.pyseco.db_lock.release()

        return(data[0])

    def add_map(self, uid, name, author, num_cp, authortime):
        self.pyseco.db_lock.acquire()
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM map WHERE uid = %s LIMIT 1", (uid))
        data = cur.fetchone()
        if data is None:
            cur.execute("""
                    INSERT INTO map
                    (uid, name, author, num_cp, authortime)
                    VALUES (%s, %s, %s, %s, %s)""",
                    (uid, name, author, num_cp, authortime))
            cur.execute("SELECT last_insert_id()")
            data = cur.fetchone()
            if data is None:
                raise DBException("Failed to create/load map")
        cur.close()
        self.conn.commit()
        self.pyseco.db_lock.release()

        return(data[0])

    def get_record(self, mid, pid):
        self.pyseco.db_lock.acquire()
        cur = self.conn.cursor()
        cur.execute("""
                SELECT time FROM record
                WHERE pid = %s AND mid = %s LIMIT 1""",
                (pid, mid))
        self.pyseco.db_lock.release()
        data = cur.fetchone()
        cur.close()
        self.conn.commit()
        self.pyseco.db_lock.release()

        if data is None:
            return None
        else:
            return data[0]

    def get_record_list(self, mid, login):
        self.pyseco.db_lock.acquire()
        cur = self.conn.cursor()
        # Params:
        # Map ID, Map ID, Map ID, Player Login, Map ID, Map ID, Map ID
        cur.execute("""
                (SELECT (@row_number := @row_number + 1) AS rank, top.*
                FROM (SELECT record.time, player.login, player.nickname
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
                            record.mid,
                            record.pid,
                            record.time,
                            record.timestamp
                        FROM record,
                            (SELECT @row_number := 0) r
                        WHERE record.mid = %s
                        ORDER BY record.time, record.timestamp ASC
                        LIMIT 200) t,
                        player
                    WHERE player.id = t.pid
                        AND player.login = %s) x
                WHERE (x.count = 1 AND rank >= LEAST(
                    GREATEST(4,
                        (SELECT COUNT(*)
                            FROM record
                            WHERE record.mid = %s)-10),
                        200-10,
                        GREATEST(x.target_rank-5 , 4))
                    AND rank <= LEAST(
                        GREATEST(4,
                            (SELECT COUNT(*)
                                FROM record
                                WHERE record.mid = %s)),
                        200,
                        GREATEST(x.target_rank-5,4)+10))
                    OR (x.count != 1 AND rank >= GREATEST(
                        4,
                        LEAST(
                            200,
                            (SELECT COUNT(*)
                                FROM record
                                WHERE record.mid = %s)
                        )-9)));""",
                (mid, mid, mid, login, mid, mid, mid))
        data = cur.fetchall()
        cur.close()
        self.conn.commit()
        self.pyseco.db_lock.release()
        out = []

        for elem in data:
            out.append(elem[:3] +
                    (elem[3].encode().decode("unicode_escape"), ))

        return out

    # returns 0 if new record was created
    # returns previous record else
    def handle_record(self, mid, login, time, timestamp):
        retval = -1

        self.pyseco.db_lock.acquire()
        cur = self.conn.cursor()
        cur.execute("""
                SELECT (SELECT rank
                    FROM (SELECT (@row_number:=@row_number + 1) AS rank,
                            player.login
                        FROM record,
                            (SELECT @row_number := 0) r,
                            player
                        WHERE record.mid = %s
                        AND record.pid = player.id
                        ORDER BY record.time, record.timestamp ASC
                        LIMIT 200) ranks
                        WHERE login = %s) AS rank,
                    time,
                    id
                FROM record,player
                WHERE mid = %s AND pid = player.id AND login = %s LIMIT 1""",
                (mid, login, mid, login))
        data = cur.fetchone()
        print(data)
        if data is None:
            prev_rank = None
            prev_time = None
            cur.execute("""
                    INSERT INTO record (mid,pid,time,timestamp)
                    VALUES (%s,
                        (SELECT id FROM player WHERE login = %s LIMIT 1),
                        %s, %s)""",
                    (mid, login, time, timestamp))
            new_time = time
        elif time < data[1]:
            prev_rank = data[0]
            prev_time = data[1]
            cur.execute("""
                    UPDATE record
                    SET time = %s,
                    timestamp = %s
                    WHERE mid = %s
                    AND pid = (SELECT id FROM player WHERE login = %s LIMIT 1)
                    LIMIT 1""",
                    (time, timestamp, mid, login))
            new_time = time
        else:
            prev_rank = data[0]
            prev_time = data[1]
            new_time = data[1]

        cur.execute("""
                SELECT (SELECT rank
                    FROM (SELECT (@row_number:=@row_number + 1) AS rank,
                            player.login
                        FROM record,
                            (SELECT @row_number := 0) r,
                            player
                        WHERE record.mid = %s
                        AND record.pid = player.id
                        ORDER BY record.time, record.timestamp ASC
                        LIMIT 200) ranks
                        WHERE login = %s) AS rank
                FROM record,player
                WHERE mid = %s AND pid = player.id AND login = %s LIMIT 1""",
                (mid, login, mid, login))

        data = cur.fetchone()
        if data is None:
            raise DBException("Failed to handle record")

        new_rank = data[0]

        cur.close()
        self.conn.commit()
        self.pyseco.db_lock.release()

        return (prev_rank, prev_time, new_rank, new_time)
