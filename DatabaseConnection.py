import pymysql.cursors
import env


class DatabaseConnection:
    conn = None

    def __init__(self, host, username, password, database):
        self.host = host
        self.username = username
        self.password = password
        self.database = database
        self.lastRowId = 0
    # ///////////////////////////////////////////

    # def __init__(self):
    #     self.host = env.DB_HOST
    #     self.username = env.DB_UNAME
    #     self.password = env.DB_PASSWORD
    #     self.database = env.DB_NAME

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

    def executeFetchAll(self, sql, autoconnect=True):
        if(autoconnect):
            self.connect()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
                return {
                    'execute_status': True,
                    'data': cursor.fetchall()
                }

        except (pymysql.err.InternalError, pymysql.err.ProgrammingError, pymysql.err.MySQLError) as e:
            # self.insError(e)
            self.fetchError = {
                'code': e.args[0],
                'msg': e.args[1]
            }
            return {
                'execute_status': False,
                'data': [],
                'error_data': {
                    'code': e.args[0],
                    'msg': e.args[1]
                }
            }
            # print(e)
        finally:
            if(autoconnect):
                self.close()
    # ///////////////////////////////////////////

    def executeFetchOne(self, sql, autoconnect=True):
        if(autoconnect):
            self.connect()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
                return {
                    'execute_status': True,
                    'data': cursor.fetchone()
                }

        except (pymysql.err.InternalError, pymysql.err.ProgrammingError, pymysql.err.MySQLError) as e:
            # self.insError(e)
            self.fetchError = {
                'code': e.args[0],
                'msg': e.args[1]
            }
            return {
                'execute_status': False,
                'data': [],
                'error_data': {
                    'code': e.args[0],
                    'msg': e.args[1]
                }
            }
            # print(e)
        finally:
            if(autoconnect):
                self.close()

    def executeCommit(self, sql, autoconnect=True):
        if(autoconnect):
            self.connect()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
                self.lastRowId = cursor.lastrowid
                self.conn.commit()
            # self.close()
            return True
        except (pymysql.err.InternalError, pymysql.err.ProgrammingError, pymysql.err.MySQLError) as e:
            # self.insError(e.args[1])
            # print(e)
            # self.close()
            self.commitError = {
                'code': e.args[0],
                'msg': e.args[1]
            }
            return False
        finally:
            if(autoconnect):
                self.close()
    # ///////////////////////////////////////////

    def info(self):
        return 'Host: {}, Username: {}, Password: {}, DB Name: {}'. format(self.host, self.username, self.password, self.database)
    # ///////////////////////////////////////////

    def insError(self, msg):
        sql = 'insert into tb_errors(error_msg) values("{}")'
        self.executeCommit(sql.format(msg))

    def getLastCommitError(self):
        return self.commitError

    def getLastFetchError(self):
        return self.fetchError
