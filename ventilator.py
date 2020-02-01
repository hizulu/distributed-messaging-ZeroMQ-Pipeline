import zmq
import random
import time
import os
import platform
import json
import env
from encryption import AES256
from DatabaseConnection import DatabaseConnection
from systemlog import SystemLog
import hashlib
import sys


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
        self.db = DatabaseConnection(
            env.DB_HOST, env.DB_UNAME, env.DB_PASSWORD, env.DB_NAME)
        self.syslog = SystemLog()
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
            # proses mengecek pesan yang valid
            # pengecekan dilakukan agar sebuah pesan tidak kembali ke pengirimnya
            # atau terjadi looping data terus menerus
            isValid = False
            if(item['msg_type'] == 'INS' or item['msg_type'] == 'DEL' or item['msg_type'] == 'UPD'):
                if(item['msg_type'] == 'INS' or item['msg_type'] == 'DEL'):
                    # mengecek pesan ins valid menggunakan
                    # PK, client_unique_id dan nama tabel
                    # sistem tidak akan mengirim data yang sama balik lagi ke   pengirimnya
                    isInsideInboxQuery = "select * from tb_sync_inbox where client_unique_id={} and result_primary_key = {} and table_name = '{}' and msg_type='{}' and is_process = 1".format(
                        item['client_unique_id'], item['row_id'], item['table_name'], item['msg_type'])

                elif(item['msg_type'] == 'UPD'):
                    isInsideInboxQuery = "select * from tb_sync_inbox where client_unique_id={} and row_id = {} and table_name = '{}' and msg_type='UPD' and md5(query) = '{}' and is_process = 1".format(
                        item['client_unique_id'], item['row_id'], item['table_name'], hashlib.md5(item['query'].encode()).hexdigest())

                inbox = self.db.executeFetchAll(
                    isInsideInboxQuery)

                clients = []
                if(inbox['execute_status']):
                    for client in inbox['data']:
                        clients.append(client['client_unique_id'])

                    if(item['client_unique_id'] not in clients):
                        isValid = True
                else:
                    self.syslog.insert("ventilator-valid-msg",
                                       "Error get data from outbox")
            else:
                isValid = True

            print(isValid)
            # sys.exit()
            if(isValid):
                packet = {
                    'client_id': item['client_unique_id'],
                    'client_key': item['client_key'],
                    'client_iv': item['client_iv'],
                    'client_port': item['client_port'],
                    'client_ip': item['client_ip'],
                    'msg_type': item['msg_type'],
                    'row_id': item['row_id'],
                    'table_name': item['table_name'],
                    'msg_id': item['outbox_id'],
                    'unix_timestamp': item['unix_timestamp'],
                    'query': item['query'],
                    'timestamp': item['created_at'].strftime("%Y-%m-%d, %H:%M:%S")
                }

                self.sender.send_json(packet)
            else:
                query = "update tb_sync_outbox set status='canceled' where outbox_id = {}".format(
                    item['outbox_id'])

                self.db.executeCommit(query)
            # self.sender.send_string(json.dumps(encryptedPacket))
