import sys
import time
import zmq
import json
from encryption import AES256
import env
from DatabaseConnection import DatabaseConnection


class Sink:
    data = None

    def __init__(self):
        self.key = env.SECRET_KEY
        self.iv = env.IV_KEY
        self.context = zmq.Context()
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.bind("tcp://127.0.0.1:5558")
        self.db = DatabaseConnection(
            'localhost', 'rama', 'ramapradana24', 'db_ta_monitor')

    def recv_json(self):
        msg = self.receiver.recv_json()
        enc = AES256()
        plain = json.loads(enc.decrypt(self.iv, msg['data'], self.key))
        msg['data'] = plain[0]
        self.data = msg
        return msg

    def auth(self):
        if(self.data['sender_id'] != self.data['data']['sender_id']):
            return False
        return True


sink = Sink()
while True:
    s = sink.recv_json()
    print(s)
    # authenticate message
    if(not sink.auth()):
        continue

    # insert message to db
    sql = """
        insert into tb_inbox(row_id, `query`, `type`, client_id, unix_timestamp)
        values({},"{}", {}, {}, {})
    """
    insert = sink.db.executeCommit(sql.format(
        s['data']['row_id'], s['data']['data'], s['data']['type'], s['data']['sender_id'], s['data']['unix_timestamp']))

    # send back which message is received using worker

    print("end time: {}".format(int(round(time.time() * 1000))))
