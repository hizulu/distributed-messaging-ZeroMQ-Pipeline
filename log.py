import pymysql.cursors
from DatabaseConnection import DatabaseConnection


class Log:
    db = None
    host = 'localhost'
    username = 'rama'
    password = 'ramapradana24'
    database = 'db_ta_monitor'
    rowLimit = '200'

    def __init__(self):
        self.db = DatabaseConnection(self.host, self.username,
                                     self.password, self.database)
    # ///////////////////////////////////////////

    def getUnproceessLog(self):
        query = 'select * from tb_outbox join tb_client on tb_client.client_id = tb_outbox.client_id where is_sent = 0 limit ' + self.rowLimit
        return self.db.executeFetchAll(query)
    # ///////////////////////////////////////////
    


    
