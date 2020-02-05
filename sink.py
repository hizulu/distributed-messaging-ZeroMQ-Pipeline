import sys
import time
import datetime
import zmq
import json
from encryption import AES256
import env
from DatabaseConnection import DatabaseConnection
from systemlog import SystemLog


class Sink:
    data = None

    def __init__(self):
        self.key = env.SECRET_KEY
        self.iv = env.IV_KEY
        self.context = zmq.Context()
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.bind(env.SINK_ADDR)
        self.syslog = SystemLog()
        self.db = DatabaseConnection(
            env.DB_HOST, env.DB_UNAME, env.DB_PASSWORD, env.DB_NAME)

    def recv_json(self):
        msg = self.receiver.recv_json()
        enc = AES256()
        plain = json.loads(enc.decrypt(self.iv, msg['data'], self.key))
        msg['data'] = plain[0]
        self.data = msg
        return msg

    def auth(self):
        if(int(self.data['sender_id']) != int(self.data['data']['sender_id'])):
            return False
        return True


sink = Sink()
while True:
    s = sink.recv_json()
    print(s)
    # authenticate message
    # if(not sink.auth()):
    #     continue
    sink.db.connect()
    # check msg apakah pesan tersebut sudah pernah masuk
    # atau tidak
    accepted = False
    checkMsgQuery = """
        select ifnull(count(*), 0) as total from tb_sync_inbox where msg_id = {} and client_unique_id = {}
    """
    checkMsg = sink.db.executeFetchOne(autoconnect=False, sql=checkMsgQuery.format(
        s['data']['msg_id'], s['data']['sender_id']))
    if(checkMsg['execute_status']):
        if(checkMsg['data']['total'] <= 0):
            accepted = True
    else:
        sink.syslog.insert(
            "accepted-msg", "Execute Error: {}".format(checkMsg['error_data']['msg']))

    # insert message to db
    if(accepted):
        sql = """
            insert into tb_sync_inbox(row_id, table_name, msg_id, `query`, `msg_type`, client_unique_id, master_status, unix_timestamp)
            values({}, "{}", {},"{}", "{}", {}, {}, {})
        """

        insert = sink.db.executeCommit(autoconnect=False, sql=sql.format(
            s['data']['row_id'], s['data']['table_name'], s['data']['msg_id'], s['data']['data'], s['data']['msg_type'], s['data']['sender_id'], s['data']['master_status'], s['data']['unix_timestamp']))
        print(insert)

        # send back which message is received using worker
        # only reply non-ACK msg
        if(s['data']['msg_type'] != 'ACK'):
            ackQuery = """
            insert into tb_sync_outbox(row_id, table_name, msg_type, query, client_unique_id, unix_timestamp, created_at, updated_at)
            values({}, "{}", "{}", {}, {}, {}, "{}", "{}")
            """

            data = s['data']
            unix_timestamp = int(time.time())
            dttime = datetime.datetime.utcfromtimestamp(
                unix_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            sink.db.executeCommit(autoconnect=False, sql=ackQuery.format(
                0, data['table_name'], "ACK", data['msg_id'], data['sender_id'], unix_timestamp, dttime, dttime))

    sink.db.close()
    print("end time: {}".format(int(round(time.time() * 1000))))
