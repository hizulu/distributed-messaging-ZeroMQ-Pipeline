import sys
import time
import zmq
import os
import sys
import json
import env
from encryption import AES256
from DatabaseConnection import DatabaseConnection
import time
from outbox import Outbox

uniqueId = env.UNIQUE_ID
db = DatabaseConnection(env.DB_HOST, env.DB_UNAME,
                        env.DB_PASSWORD, env.DB_NAME)
outbox = Outbox(db)
# if(len(sys.argv) == 2):
#     fileName = sys.argv[1]
# else:
#     fileName = 'worker_process.id'

# print(fileName)
context = zmq.Context()
# f = open("process/"+fileName, "a+")
# f.write(str(os.getpid()) + "\n")
# f.close()
# Socket to receive messages on
receiver = context.socket(zmq.PULL)
receiver.connect("tcp://localhost:5557")


while True:
    s = receiver.recv_json()

    # labeling row as processed
    # updateQuery = """
    #     update tb_sync_outbox set is_sent=1, status='sent' where outbox_id = {}
    # """
    if(outbox.update(data={'is_sent': 1, 'status': 'sent'},
                     where_clause={'outbox_id': s['msg_id']})):
        print('sukses')
    else:
        print('gagal')

    enc = AES256()
    jsonPacket = {
        'query': s['query'],
        'sender_id': uniqueId,
        'timestamp': s['timestamp'],
        'occur_at': s['occur_at'],
        'first_time_occur_at': s['first_time_occur_at'],
        'row_id': s['row_id'],
        'table_name': s['table_name'],
        'msg_id': s['msg_id'],
        'msg_type': s['msg_type'],
        'master_status': 1 if env.MASTER_NODE == True else 0
    },
    data = enc.encrypt(json.dumps(jsonPacket), s['client_key'], s['client_iv'])
    # data = jsonPacket
    encryptedPacket = {
        'sender_id': uniqueId,
        'data': data
    }

    url = "tcp://" + s['client_ip'] + ":" + str(s['client_port'])
    sender = context.socket(zmq.PUSH)
    sender.connect(url)
    sender.send_json(encryptedPacket)
