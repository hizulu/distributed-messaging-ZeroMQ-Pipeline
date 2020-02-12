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
        sync_token = data['sync_token'] if 'sync_token' in data else '(NULL)'
        priority = data['priority'] if 'priority' in data else 2
        # result_primary_key = data['result_primary_key'] if 'result_primary_key' in data else 0
        master_status = data['master_status']
        unix_timestamp = data['occur_at'] if 'occur_at' in data else int(
            time.time())
        first_time_occur_at = data['first_time_occur_at'] if 'first_time_occur_at' in data else datetime.datetime.now(
        ).strftime('%Y-%m-%d %H:%M:%S')
        dttime = datetime.datetime.utcfromtimestamp(
            unix_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        sql = """
            insert into tb_sync_inbox(row_id, table_name, msg_type, msg_id, query, client_unique_id, master_status, occur_at, first_time_occur_at, created_at, updated_at, priority, sync_token)
            values("{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}", "{}", "{}")
        """

        return self.db.executeCommit(sql=sql.format(row_id, table_name, msg_type, msg_id, query, client_unique_id, master_status, unix_timestamp, first_time_occur_at, dttime, dttime, priority, sync_token))

    def update(self, data, where_clause):
        query = 'update tb_sync_inbox set '
        column_count = len(data)
        where_count = len(where_clause)
        i = 0

        # set new value
        for key in data:
            i += 1
            query += "{}='{}'".format(key, data[key])
            if(i < column_count):
                query += ', '

        # add where clouse
        query += ' where '
        i = 0
        for key in where_clause:
            i += 1
            query += "{}='{}'".format(key, where_clause[key])
            if(i < where_count):
                query += ' and '

        return self.db.executeCommit(query)
