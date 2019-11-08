import sys
import time
import zmq
import json
from encryption import AES256
from DatabaseConnection import DatabaseConnection


class Sink:
    key = 'sice2lrit9q2wvzx'
    iv = '6YM6LfUkMAx6A27U'
    data = None

    def __init__(self):
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
    valid = sink.auth()
    if(not valid):
        continue

    # insert message to db
    sql = """
        insert into tb_inbox(`query`, `type`, client_id)
        values("{}", {}, {})
    """
    sink.db.executeCommit(sql.format(
        s['data']['data'], s['data']['type'], s['data']['sender_id']))
    print("end time: {}".format(int(round(time.time() * 1000))))
