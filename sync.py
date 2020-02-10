from DatabaseConnection import DatabaseConnection
import env
import sys
from outbox import Outbox
from systemlog import SystemLog
from inbox import Inbox
import json
import time


class Sync:

    def __init__(self):
        self.syncDB = DatabaseConnection(
            env.DB_HOST, env.DB_UNAME, env.DB_PASSWORD, env.DB_NAME)
        self.limitRow = env.LIMIT_PROC_ROW
        self.outbox = Outbox(self.syncDB)
        self.systemlog = SystemLog()
        self.inbox = Inbox(self.syncDB)
        self.outbox = Outbox(self.syncDB)

    def getClient(self):
        sql = "select * from tb_sync_client"
        return self.syncDB.executeFetchAll(sql)

    def setPriority(self, id, table, priority):
        db_name = env.DB_NAME
        sql = """
            select COLUMN_NAME from information_schema.COLUMNS
            where TABLE_SCHEMA='{}' and TABLE_NAME='{}'
            and COLUMN_KEY='PRI'
        """.format(db_name, table)
        res = self.syncDB.executeFetchOne(sql)
        if(res['execute_status']):
            primary_key = res['data']['COLUMN_NAME']
            # update primary key
            sql = "update {} set priority={} where {}={}"
            update = self.syncDB.executeCommit(
                sql.format(table, priority, primary_key, id))

            if(update):
                # update PK success
                print("Updated Priority")
            else:
                self.systemlog.insert(
                    "Sync.setPriority", json.dumps(self.syncDB.getLastCommitError()))

    def processInsert(self, data):
        print('Processing inbox: {}'.format(data['inbox_id']), end=": ")
        insert = self.syncDB.executeCommit(data['query'])
        if(insert):
            print('success')
            rowId = self.syncDB.lastRowId

            # set result primary key to table inbox
            insert = self.inbox.update(data={
                'result_primary_key': rowId,
            }, where_clause={
                'inbox_id': data['inbox_id']
            })

            # if the msg is sent from master
            # update primary key right away
            if(data['master_status'] == 1):
                # insert to inbox jadi akan dikerjakan di proses selanjutnya
                inbox = {
                    'row_id': rowId,
                    'table_name': data['table_name'],
                    'msg_type': 'PRI',
                    'msg_id': 0,
                    'query': data['row_id'],
                    'client_unique_id': 0,
                    'master_status': 0
                }
                if(not self.inbox.insert(inbox)):
                    print(self.syncDB.getLastCommitError())
            elif(env.MASTER_NODE):
                # master akan mengirim PK hasil insert ke
                # slave pengirim pesan insert
                msg = {
                    'row_id': data['row_id'],  # local row id
                    'table_name': data['table_name'],
                    'msg_type': 'PRI',
                    'query': rowId,  # receiver outbox_id
                    'client_unique_id': data['client_unique_id'],
                    'msg_id': 0,
                }
                self.outbox.insert(msg)
            self.setAsProcessed(data['inbox_id'])
        else:
            # set priority menjadi 3
            self.setPriority(data['inbox_id'], 'tb_sync_inbox', 3)
            print('error')
        return True

    # method ini digunakan untuk memproses update primary key
    # primary key yang digunakan adalah primary key dari master
    def processPrimaryKey(self, data):
        # mencari nama kolom primary key
        # print(db_name)
        db_name = env.DB_NAME
        sql = """
            select COLUMN_NAME from information_schema.COLUMNS
            where TABLE_SCHEMA='{}' and TABLE_NAME='{}'
            and COLUMN_KEY='PRI'
        """.format(db_name, data['table_name'])
        res = self.syncDB.executeFetchOne(sql)
        if(res['execute_status']):
            primary_key = res['data']['COLUMN_NAME']
            # update primary key
            sql = "update {} set {}={} where {}={}"
            update = self.syncDB.executeCommit(sql.format(
                data['table_name'], primary_key, data['query'], primary_key, data['row_id']))

            if(update):
                # update PK success
                print("Updated PK")
                self.setAsProcessed(data['inbox_id'])
            else:
                self.setPriority(data['inbox_id'], 'tb_sync_inbox', 3)
                self.systemlog.insert(
                    "Sync.processPrimaryKey", json.dumps(self.syncDB.getLastCommitError()))

    def processUpdate(self, data):
        return True

    def processDelete(self, data):
        return True

    def processAck(self, data):
        ack = self.outbox.update(data={
            'is_arrived': 1,
            'status': 'arrived'
        }, where_clause={
            'outbox_id': data['query']
        })
        # ackQuery = "update tb_sync_outbox set is_arrived=1, status='arrived' where outbox_id = {}".format(
        #     data['query'])
        # ack = self.syncDB.executeCommit(ackQuery)
        if(not ack):
            self.setPriority(data['inbox_id'], 'tb_sync_inbox', 3)
            self.outbox.update(data={'is_error': 1}, where_clause={
                               'outbox_id': data['msg_id']})
            # errorQuery = 'update tb_sync_outbox set is_error=1 where outbox_id = {}'.format(
            #     data['msg_id'])
            # self.syncDB.executeCommit(errorQuery)

            self.systemlog.insert("processACK", "Gagal update ACK ID#{} ERROR: {}".format(
                data['inbox_id'], self.syncDB.getLastCommitError()['msg']))
        else:
            self.setAsProcessed(data['inbox_id'])
        return True

    def getData(self):
        self.syncDB.connect()
        sql = "select * from tb_sync_inbox where is_process = 0 limit " + \
            str(self.limitRow)
        data = self.syncDB.executeFetchAll(sql, False)
        self.syncDB.close()
        return data

    def setAsProcessed(self, id):
        set = self.inbox.update(
            data={'is_process': 1}, where_clause={'inbox_id': id})
        # query = 'update tb_sync_inbox set is_process=1 where inbox_id = {}'.format(
        #     id)
        print(set)

    def reply(self, code, msg):
        return True


sync = Sync()
# sync.setPriority(2677, 'tb_sync_outbox', 2)
# sync.db.insError("test")
# sys.exit()
while True:
    inbox = sync.getData()
    if(inbox['execute_status']):
        if(inbox['data']):
            for item in inbox['data']:
                print("Processing: {}".format(item['inbox_id']))
                msgType = item['msg_type']
                if(msgType == 'INS'):
                    sync.processInsert(item)
                elif(msgType == 'UPD'):
                    sync.processUpdate(item)
                elif(msgType == 'DEL'):
                    sync.processDelete(item)
                elif(msgType == 'ACK'):
                    sync.processAck(item)
                elif(msgType == "PRI"):
                    sync.processPrimaryKey(item)
                else:
                    sync.syncDB.insError("Msg type not found for id=" +
                                         str(item['inbox_id']))
        else:
            time.sleep(1)
    else:
        print('Error')
        sys.exit()
