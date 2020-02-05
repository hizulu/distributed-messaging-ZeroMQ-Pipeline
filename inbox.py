from DatabaseConnection import DatabaseConnection
import datetime
import time


class Inbox:
    def __init__(self, db):
        self.db = db

    def insert(self, data):
        row_id = data['row_id']
        table_name = data['table_name']
        msg_type = data['msg_type']
        msg_id = data['msg_id']
        query = data['query']
        client_unique_id = data['client_unique_id']
        result_primary_key = data['result_primary_key'] if 'result_primary_key' in data else 0
        master_status = data['master_status']
        unix_timestamp = int(time.time())
        dttime = datetime.datetime.utcfromtimestamp(
            unix_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        sql = """
            insert into tb_sync_inbox(row_id, table_name, msg_type, msg_id, query, client_unique_id, master_status, unix_timestamp, created_at, updated_at, result_primary_key)
            values('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')
        """

        return self.db.executeCommit(sql=sql.format(row_id, table_name, msg_type, msg_id, query, client_unique_id, master_status, unix_timestamp, dttime, dttime))
