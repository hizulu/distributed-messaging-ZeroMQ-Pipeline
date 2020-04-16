import pymysql.cursors
import env
from DatabaseConnection import DatabaseConnection
import datetime


class Log:
    db = None
    host = 'localhost'
    username = 'rama'
    password = 'ramapradana24'
    database = 'db_ta_monitor'

    def __init__(self):
        self.rowLimit = env.LOG_ROW_LIMIT
        self.db = DatabaseConnection(
            env.DB_HOST, env.DB_UNAME, env.DB_PASSWORD, env.DB_NAME)
    # ///////////////////////////////////////////

    def getUnproceessLog(self):
        query = f"""select * from tb_sync_outbox
            where (status = 'waiting') or
            (status = 'sent' and retry_again_at <= now()) 
            order by first_time_occur_at asc, priority asc"""
        if (env.LOG_ROW_LIMIT > 0):
            query += f' limit {env.LOG_ROW_LIMIT}'
        result = self.db.executeFetchAll(sql=query)
        return result
    # ///////////////////////////////////////////
