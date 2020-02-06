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
        self.db = DatabaseConnection(
            env.DB_HOST, env.DB_UNAME, env.DB_PASSWORD, env.DB_NAME)
    # ///////////////////////////////////////////

    def getUnproceessLog(self):
        query = """
            select * from tb_sync_outbox 
            join tb_sync_client on tb_sync_client.client_unique_id = tb_sync_outbox.client_unique_id 
            where is_sent = 0 and status = 'waiting' limit {} order by first_time_occur_at asc""".format(self.rowLimit)
        result = self.db.executeFetchAll(sql=query)
        return result
    # ///////////////////////////////////////////
