import pymysql.cursors


class DatabaseConnection:
    conn = None

    def __init__(self, host, username, password, database):
        self.host = host
        self.username = username
        self.password = password
        self.database = database
    # ///////////////////////////////////////////

    def connect(self):
        self.conn = pymysql.connect(
            host=self.host,
            user=self.username,
            password=self.password,
            db=self.database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    # ///////////////////////////////////////////

    def close(self):
        if(self.conn != None):
            self.conn.close()
    # ///////////////////////////////////////////

    def executeFetchAll(self, sql):
        self.connect()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
                return cursor.fetchall()
        finally:
            self.close()
    # ///////////////////////////////////////////

    def executeCommit(self, sql):
        self.connect()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
                self.conn.commit()

        finally:
            self.close()
    # ///////////////////////////////////////////

    def info(self):
        return 'Host: {}, Username: {}, Password: {}, DB Name: {}'. format(self.host, self.username, self.password, self.database)
    # ///////////////////////////////////////////
