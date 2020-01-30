from DatabaseConnection import DatabaseConnection
import env


class SystemLog:

    def __init__(self):
        self.db = DatabaseConnection(
            env.DB_HOST, env.DB_UNAME, env.DB_PASSWORD, 'db_ta1')

    def insert(self, function_name, msg):
        sql = """
            insert into tb_sync_log(log_function, log_msg)
            values('{}', '{}')
        """
        self.db.executeCommit(sql.format(function_name, msg))
