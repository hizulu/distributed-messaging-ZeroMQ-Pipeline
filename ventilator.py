import zmq
import random
import time
import os
import platform
import json
import env
from encryption import AES256


class Ventilator:
    context = None
    sender = None
    processId = None
    system = None

    def __init__(self):
        self.maxRowPerWorker = env.VEN_MAX_ROW_PER_WORKER
        self.workerAddress = env.VEN_WORKER_ADDR
        self.sinkAddr = env.SINK_ADDR
        self.context = zmq.Context()
        self.sender = self.context.socket(zmq.PUSH)
        self.sender.bind(self.workerAddress)
        self.processId = os.getpid()
        self.system = platform.system()
    # ///////////////////////////////////////////

    def setWorker(self, numberOfWorker):
        for i in range(numberOfWorker):
            os.system('py worker.py ' + self.processId)
    # ///////////////////////////////////////////

    def killWorker(self):
        file = open("process/" + self.processId)
        workers = file.read()
        print(workers)
    # ///////////////////////////////////////////

    def send(self, data):
        sink = self.context.socket(zmq.PUSH)
        sink.connect(self.sinkAddr)
        i = 1
        for item in data:
            packet = {
                'client_id': item['client_unique_id'],
                'client_key': item['client_key'],
                'client_iv': item['client_iv'],
                'client_port': item['client_port'],
                'client_ip': item['client_ip'],
                'msg_type': item['msg_type'],
                'row_id': item['row_id'],
                'msg_id': item['outbox_id'],
                'unix_timestamp': item['unix_timestamp'],
                'query': item['query'],
                'timestamp': item['created_at'].strftime("%Y-%m-%d, %H:%M:%S")
            }

            self.sender.send_json(packet)
            print("{} ".format(i))
            i += 1
            # self.sender.send_string(json.dumps(encryptedPacket))
