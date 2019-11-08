import sys
import time
import zmq
import os
import sys
import json
from encryption import AES256
import time

uniqueId = 234

if(len(sys.argv) == 2):
    fileName = sys.argv[1]
else:
    fileName = 'worker_process.id'

print(fileName)
context = zmq.Context()
f = open("process/"+fileName, "a+")
f.write(str(os.getpid()) + "\n")
f.close()
# # Socket to receive messages on
receiver = context.socket(zmq.PULL)
receiver.connect("tcp://localhost:5557")


while True:
    s = receiver.recv_json()

    enc = AES256()
    jsonPacket = {
        'data': s['query'],
        'sender_id': uniqueId,
        'timestamp': s['timestamp'],
        'type': s['type']
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
