import pymysql.cursors
import env
from DatabaseConnection import DatabaseConnection


class Log:
    db = None
    host = 'localhost'
    username = 'rama'
    password = 'ramapradana24'
    database = 'db_ta_monitor'

    def __init__(self):
        self.rowLimit = env.LOG_ROW_LIMIT
        self.db = DatabaseConnection(env.DB_HOST, env.DB_UNAME,
                                     env.DB_PASSWORD, env.DB_NAME)
    # ///////////////////////////////////////////

    def getUnproceessLog(self):
        query = """
            select * from tb_outbox 
            join tb_client on tb_client.client_id = tb_outbox.client_id 
            where is_sent = 0 limit """ + self.rowLimit
        return self.db.executeFetchAll(query)
    # ///////////////////////////////////////////
