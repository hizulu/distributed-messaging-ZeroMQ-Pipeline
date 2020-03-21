from DatabaseConnection import DatabaseConnection
import datetime
import time
import env


class Outbox:
    def __init__(self, db=None):
        self.db = db
        self.nextRetryAdditionalSecond = 30

    def insert(self, data):
        # primary key of table associated. primary key of receiver if ACK,
        # PK of sender if ACK-PROC (tell the sender that the msg is successfully run)
        rowId = data['row_id']
        table_name = data['table_name']
        msg_type = data['msg_type']
        sync_token = data['sync_token'] if 'sync_token' in data else '(NULL)'
        # msg_id is receiver outbox_id for this msg
        msg_id = data['msg_id']
        string_query = data['query']
        priority = data['priority'] if 'priority' in data else 2
        # client_uid = receiver id
        client_uid = data['client_unique_id']
        unix_timestamp = data['occur_at'] if 'occur_at' in data else time.time(
        )
        first_time_occur_at = data['first_time_occur_at'] if 'first_time_occur_at' in data else time.time(
        )

        time_at = datetime.datetime.utcfromtimestamp(
            unix_timestamp)
        dttime = time_at.strftime('%Y-%m-%d %H:%M:%S')
        nextRetry = time_at + \
            datetime.timedelta(seconds=self.nextRetryAdditionalSecond)
        nextRetry = nextRetry.strftime('%Y-%m-%d %H:%M:%S')
        # print(f"time: {dttime} next: {nextRetry}")
        if (client_uid == 0):
            query = """
                insert into tb_sync_outbox(row_id, table_name, msg_type, msg_id, query, client_unique_id, occur_at, first_time_occur_at, created_at, updated_at, priority, sync_token, client_ip, client_port, client_key, client_iv, retry_again_at)
                values("{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}")
            """ .format(rowId, table_name, msg_type, msg_id, string_query, client_uid, unix_timestamp, first_time_occur_at, dttime, dttime, priority, sync_token, data['client_ip'], data['client_port'], data['client_key'], data['client_iv'], nextRetry)
        else:
            query = """
                insert into tb_sync_outbox(row_id, table_name, msg_type, msg_id, query, client_unique_id, occur_at, first_time_occur_at, created_at, updated_at, priority, sync_token, retry_again_at)
                values("{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}")
            """.format(rowId, table_name, msg_type, msg_id, string_query, client_uid, unix_timestamp, first_time_occur_at, dttime, dttime, priority, sync_token, nextRetry)

        ins = self.db.executeCommit(sql=query)
        if not ins:
            print(self.db.getLastCommitError())

        return ins

    def update(self, data, where_clause):
        query = 'update tb_sync_outbox set '
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

        # print(query)
        exe = self.db.executeCommit(query)
        # print(self.db.getLastCommitError())
        return exe


# out = Outbox()
# out.insert(data={
#     'row_id': 1,
#     'table_name': "hehe",
#     'msg_type': 'REG',
#     'msg_id': 1,
#     'query': 'hehehe',
#     'client_unique_id': 12
# })
