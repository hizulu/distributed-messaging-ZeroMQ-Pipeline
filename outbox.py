from DatabaseConnection import DatabaseConnection
import datetime
import time


class Outbox:
    def __init__(self, db):
        self.db = db

    def insert(self, data):
        # primary key of table associated. primary key of receiver if ACK,
        # PK of sender if ACK-PROC (tell the sender that the msg is successfully run)
        rowId = data['row_id']
        table_name = data['table_name']
        msg_type = data['msg_type']
        # msg_id is receiver outbox_id for this msg
        msg_id = data['msg_id']
        string_query = data['query']
        # client_uid = receiver id
        client_uid = data['client_unique_id']
        unix_timestamp = int(time.time())
        dttime = datetime.datetime.utcfromtimestamp(
            unix_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        query = """
            insert into tb_sync_outbox(row_id, table_name, msg_type, msg_id, query, client_unique_id, unix_timestamp, created_at, updated_at)
            values({}, "{}", "{}", {}, "{}", {}, {}, "{}", "{}")
        """.format(rowId, table_name, msg_type, msg_id, string_query, client_uid, unix_timestamp, dttime, dttime)

        self.db.executeCommit(sql=query)
