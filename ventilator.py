import zmq
import random
import time
import os
import platform
import json
from encryption import AES256


class Ventilator:
    context = None
    maxRowPerWorker = 50
    sender = None
    workerAddress = "tcp://*:5557"
    processId = None
    system = None

    def __init__(self):
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
        print()
        sink = self.context.socket(zmq.PUSH)
        sink.connect("tcp://localhost:5558")
        i = 1
        for item in data:
            packet = {
                'client_id': item['client_unique_id'],
                'client_key': item['client_key'],
                'client_iv': item['client_iv'],
                'client_port': item['client_port'],
                'client_ip': item['client_ip'],
                'type': item['type'],
                'query': item['query'],
                'timestamp': item['created_at'].strftime("%Y-%m-%d, %H:%M:%S")
            }

            self.sender.send_json(packet)
            print("{} ".format(i))
            i += 1
            # self.sender.send_string(json.dumps(encryptedPacket))
