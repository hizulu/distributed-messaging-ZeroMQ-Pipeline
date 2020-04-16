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
from outbox import Outbox
import datetime


class Ventilator:
    context = None
    sender = None
    processId = None
    system = None

    def __init__(self):
        # self.maxRowPerWorker = env.VEN_MAX_ROW_PER_WORKER
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
        self.outbox = Outbox(self.db)
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
            print("[{}] -> #{} to {} ->".format(datetime.datetime.now().strftime(
                "%d-%m-%Y %H:%M:%S"), item['outbox_id'], item['client_unique_id']), end=" ")
            isValid = False
            invalidReason = 'Loop'
            if(item['msg_type'] == 'INS' or item['msg_type'] == 'DEL' or item['msg_type'] == 'UPD'):
                if(item['msg_type'] == 'INS' or item['msg_type'] == 'DEL'):
                    # mengecek pesan ins valid menggunakan
                    # PK, client_unique_id dan nama tabel
                    # sistem tidak akan mengirim data yang sama balik lagi ke   pengirimnya
                    isInsideInboxQuery = "select * from tb_sync_inbox where client_unique_id={} and sync_token = '{}' and table_name = '{}' and msg_type='{}'".format(
                        item['client_unique_id'], item['sync_token'], item['table_name'], item['msg_type'])

                elif(item['msg_type'] == 'UPD'):
                    isInsideInboxQuery = "select * from tb_sync_inbox where client_unique_id={} and sync_token = '{}' and table_name = '{}' and msg_type='{}'".format(
                        item['client_unique_id'], item['sync_token'], item['table_name'], item['msg_type'])

                inbox = self.db.executeFetchAll(
                    isInsideInboxQuery)

                if(inbox['execute_status']):
                    clients = [client['client_unique_id']
                               for client in inbox['data']]
                    print(clients)
                    if(item['client_unique_id'] not in clients):
                        isValid = True

                    # filter DEL msg type
                    # jangan kirim pesan DEL jika row yang di DEL belum selesai
                    if(not env.MASTER_MODE and item['msg_type'] == 'DEL'):
                        checkPRIQuery = """
                            select * from tb_sync_inbox where msg_type = 'PRI'
                            and status='waiting'
                            and table_name = '{}' and row_id = '{}'
                        """
                        checkPRIRes = self.db.executeFetchAll(
                            checkPRIQuery.format(item['table_name'], item['query']))

                        if(checkPRIRes['execute_status']):
                            if(len(checkPRIRes['data']) > 0):
                                isValid = False
                                invalidReason = "PRI not yet process"
                            else:
                                isValid = True
                        else:
                            isValid = False
                            invalidReason = "Check PRI fail"
                else:
                    self.syslog.insert("ventilator-valid-msg",
                                       "Error get data from outbox")
            else:
                isValid = True

            # print(isValid)
            # sys.exit()
            if(isValid):
                print('valid, Reason: {}'.format(invalidReason))
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
                    'occur_at': item['occur_at'],
                    'sync_token': item['sync_token'],
                    'first_time_occur_at': item['first_time_occur_at'],
                    'query': item['query'],
                    'priority': item['priority'],
                    'timestamp': item['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                }
                nextRetryAt = datetime.datetime.now() + datetime.timedelta(seconds=30)
                nextRetryAt = nextRetryAt.strftime('%Y-%m-%d %H:%M:%S')
                if (item['msg_type'] == 'ACK'):
                    status = 'arrived'
                else:
                    status = 'sent'
                self.outbox.update(data={'priority': 3, 'status': status, 'retry_again_at': nextRetryAt}, where_clause={
                                   'outbox_id': item['outbox_id']})
                self.sender.send_json(packet)

                file = open("sendtime.txt", 'a')
                file.write(f"{time.time()}\n")
                file.close()

            else:
                print('invalid, Reason: {}'.format(invalidReason))
                # self.outbox.update(data={'status': 'canceled'}, where_clause={
                #                    'outbox_id': item['outbox_id']})
                query = "update tb_sync_outbox set status='canceled' where outbox_id = {}".format(
                    item['outbox_id'])

                self.db.executeCommit(query)
            # self.sender.send_string(json.dumps(encryptedPacket))
