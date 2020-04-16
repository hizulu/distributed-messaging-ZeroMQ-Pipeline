import sys
import time
import datetime
import zmq
import json
from encryption import AES256
import env as env
from DatabaseConnection import DatabaseConnection
from systemlog import SystemLog
from inbox import Inbox
from outbox import Outbox
import os
from threading import Thread


class Sink:
    data = None

    def __init__(self, dbhost, dbusername, dbpass, dbname, sinkaddr, skey, ivkey):
        self.key = skey
        self.iv = ivkey
        self.context = zmq.Context()
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.bind(sinkaddr)
        self.syslog = SystemLog()
        self.db = DatabaseConnection(
            dbhost, dbusername, dbpass, dbname)
        self.inbox = Inbox(self.db)
        self.outbox = Outbox(self.db)

    def recv_json(self):
        msg = self.receiver.recv_json()
        enc = AES256()
        try:
            plain = json.loads(enc.decrypt(self.iv, msg['data'], self.key))
        except json.decoder.JSONDecodeError as identifier:
            return {
                'error': 'Invalid secret key or IV key'
            }

        msg['data'] = plain[0]
        self.data = msg
        return msg

    def auth(self):
        if(int(self.data['sender_id']) != int(self.data['data']['sender_id'])):
            return False
        return True

    def recvAck(self, data):
        conn = DatabaseConnection(
            env.DB_HOST, env.DB_UNAME, env.DB_PASSWORD, env.DB_NAME)
        obox = conn.executeFetchOne(
            f"select * from tb_sync_outbox where outbox_id = {data['query']}")
        ack = True
        if(obox['data']):
            if (obox['data']['msg_type'] == 'INS'):
                status = 'need_pk_update'
            else:
                status = 'arrived'

            # ack = self.outbox.update(data={
            #     'status': status
            # }, where_clause={
            #     'outbox_id': data['query']
            # })
            ack = conn.executeCommit(
                f"update tb_sync_outbox set status='{status}' where outbox_id={data['query']}")


sink = Sink(env.DB_HOST, env.DB_UNAME, env.DB_PASSWORD,
            env.DB_NAME, env.SINK_ADDR, env.SECRET_KEY, env.IV_KEY)
while True:
    s = sink.recv_json()
    # print(s)
    if ('error' in s):
        print("Invalid secret key or IV key")
    else:
        print("[{}] -> #{}".format(datetime.datetime.now().strftime(
            "%d-%m-%Y %H:%M:%S"), s['data']['msg_id']), end=" ")
        # authenticate message
        # if(not sink.auth()):
        #     continue
        # sink.db.connect()
        # check msg apakah pesan tersebut sudah pernah masuk
        # atau tidak
        accepted = False
        if (s['data']['msg_type'] != 'ACK'):
            checkMsgQuery = """
                select ifnull(count(*), 0) as total from tb_sync_inbox where msg_id = {} and client_unique_id = {}
            """
            checkMsg = sink.db.executeFetchOne(sql=checkMsgQuery.format(
                s['data']['msg_id'], s['data']['client_unique_id']))
            if(checkMsg['execute_status']):
                if(checkMsg['data']['total'] <= 0):
                    accepted = True
            else:
                sink.syslog.insert(
                    "accepted-msg", "Execute Error: {}".format(checkMsg['error_data']['msg']))
        else:
            checkMsgQuery = """
                select ifnull(count(*), 0) as total from tb_sync_inbox where msg_type = 'ACK' and client_unique_id = {} and query='{}'
            """
            checkMsg = sink.db.executeFetchOne(sql=checkMsgQuery.format(
                s['data']['client_unique_id'], s['data']['query']))
            if(checkMsg['execute_status']):
                if(checkMsg['data']['total'] <= 0):
                    accepted = True

        # insert message to db
        if (accepted):
            # print(s['data'])
            if (s['data']['msg_type'] == 'ACKS'):
                thread = Thread(target=sink.recvAck, args=(s['data'],))
                thread.start()
            else:
                insert = sink.inbox.insert(s['data'])
                if (not insert):
                    print(sink.db.getLastCommitError())
            # sql = """
            #     insert into tb_sync_inbox(row_id, table_name, msg_id, `query`, `msg_type`, client_unique_id, master_status, occur_at, first_time_occur_at)
            #     values({}, "{}", {},"{}", "{}", {}, {}, {}, {})
            # """

            # insert = sink.db.executeCommit(autoconnect=False, sql=sql.format(
            #     s['data']['row_id'], s['data']['table_name'], s['data']['msg_id'], s['data']['data'], s['data']['msg_type'], s['data']['sender_id'], s['data']['master_status'], s['data']['unix_timestamp']))
            print('accepted')
        else:
            print('rejected')

        # send back which message is received using worker
        # only reply non-ACK msg
        if(s['data']['msg_type'] != 'ACK' and s['data']['msg_type'] != 'REG'):
            data = s['data']
            sink.outbox.insert(data={
                'row_id': 0,
                'table_name': data['table_name'],
                'msg_type': 'ACK',
                'query': data['msg_id'],
                'client_unique_id': data['client_unique_id'],
                'msg_id': 0,
                'priority': 1
            })
    # print("end time: {}".format(int(round(time.time() * 1000))))
