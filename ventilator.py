import zmq
import random
import time
import os
import platform
import json


class Ventilator:
    context = None
    maxRowPerWorker = 50
    sender = None
    workerAddress = "tcp://*:5557"
    processId = None
    system = None
    uniqueId = 234

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
        sink = self.context.socket(zmq.PUSH)
        sink.connect("tcp://localhost:5558")

        for item in data:
            packet = {
                'client_id': item['client_unique_id'],
                'type': item['type'],
                'query': item['query'],
                'timestamp': item['created_at'].strftime("%Y-%m-%d, %H:%M:%S"),
                'sender_id': self.uniqueId
            }

            print(json.dumps(packet))
        # sink.send(b'rama pradana')
        # workload = random.randint(1, 100)
        # self.sender.send_string(u'%i' % workload)
