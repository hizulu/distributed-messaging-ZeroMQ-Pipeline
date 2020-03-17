from DatabaseConnection import DatabaseConnection
import env as env
import sys
from outbox import Outbox
from systemlog import SystemLog
from inbox import Inbox
import json
import time
import datetime


class Sync:

    def __init__(self):
        self.syncDB = DatabaseConnection(
            env.DB_HOST, env.DB_UNAME, env.DB_PASSWORD, env.DB_NAME)
        self.limitRow = env.LIMIT_PROC_ROW
        self.outbox = Outbox(self.syncDB)
        self.systemlog = SystemLog()
        self.inbox = Inbox(self.syncDB)
        self.outbox = Outbox(self.syncDB)
        self.clientIdStartFrom = 10

    def getClient(self):
        sql = "select * from tb_sync_client"
        return self.syncDB.executeFetchAll(sql)

    def _getPrimaryKeyColumn(self, table):
        db_name = env.DB_NAME
        sql = """
            select COLUMN_NAME from information_schema.COLUMNS
            where TABLE_SCHEMA='{}' and TABLE_NAME='{}'
            and COLUMN_KEY='PRI'
        """.format(db_name, table)
        res = self.syncDB.executeFetchOne(sql)
        return res['data']['COLUMN_NAME']

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
            print('done')
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
                    'master_status': 0,
                    'priority': 1
                }
                if(not self.inbox.insert(inbox)):
                    print(self.syncDB.getLastCommitError())
            elif(env.MASTER_MODE):
                # master akan mengirim PK hasil insert ke
                # slave pengirim pesan insert
                msg = {
                    'row_id': data['row_id'],  # local row id
                    'table_name': data['table_name'],
                    'msg_type': 'PRI',
                    'query': rowId,  # receiver outbox_id
                    'client_unique_id': data['client_unique_id'],
                    'msg_id': 0,
                    'priority': 1
                }
                tes = self.outbox.insert(msg)
                # print(tes)
                if(not tes):
                    print(self.syncDB.getLastCommitError())
            self.setAsProcessed(data['inbox_id'])
        else:
            # set priority menjadi 3
            self.setPriority(data['inbox_id'], 'tb_sync_inbox', 3)
            print('error, downgrade priority')
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

            if (update):
                # update inbox set done
                query = f"update tb_sync_outbox set status = 'done' where msg_type = 'INS' and row_id={data['row_id']} and table_name = '{data['table_name']}'"
                if (not self.syncDB.executeCommit(query)):
                    print('GAGAL SET DONE')
                # update PK success
                # cek pesan lain yang menggunakan PK lama
                # update ke PK baru
                if (not env.MASTER_MODE):
                    check = "select * from tb_sync_outbox where (status = 'waiting' or status='canceled') and (msg_type = 'DEL' or msg_type='UPD') and row_id = {}"
                    res = self.syncDB.executeFetchAll(
                        check.format(data['row_id']))
                    if(res['execute_status']):
                        # update ke PK yang benar
                        for msg in res['data']:
                            query = "update tb_sync_outbox set row_id={}, status='waiting' where outbox_id={}"
                            updated = self.syncDB.executeCommit(
                                query.format(data['query'], msg['outbox_id']))
                            if(not updated):
                                print(self.syncDB.getLastCommitError()['msg'])
                    else:
                        print("CHECK PESAN LAIN ERROR: {}".format(
                            res['error_data']['msg']))
                self.setAsProcessed(data['inbox_id'])
                print("done")
            else:
                # update primary key to 0
                # as temp
                print('error, downgrade priority')
                update = self.syncDB.executeCommit(sql.format(
                    data['table_name'], primary_key, 0, primary_key, data['row_id']))
                if(update):
                    self.inbox.update(data={
                        'priority': 3,
                        'row_id': 0,
                    }, where_clause={
                        'inbox_id': data['inbox_id']
                    })
                else:
                    self.setPriority(data['inbox_id'], 'tb_sync_inbox', 3)
                self.systemlog.insert(
                    "Sync.processPrimaryKey", json.dumps(self.syncDB.getLastCommitError()))

    def processUpdate(self, data):
        execute = self.syncDB.executeCommit(data['query'])
        if (not execute):
            print("ERROR")
        else:
            self.setAsProcessed(data['inbox_id'])
            print("OK")

    def processDelete(self, data):
        # cek apakah ada inbox yang bertipe PRI
        # berdasarkan primari key yang masuk
        # jika ada mata update inbox tersebut jadi terproses
        # jika tidak ada lakukan delete seperti biasa
        checkQuery = """
            select count(inbox_id) as total from tb_sync_inbox where msg_type = 'PRI'
            and and status = 'waiting'
            and table_name = '{}'
            and query = '{}'
        """

        result = self.syncDB.executeFetchOne(
            checkQuery.format(data['table_name'], data['query']))
        if(result['execute_status']):
            if(result['data']['total'] > 0):
                print('Skip, total PRI: {}'.format(result['data']['total']))
            else:
                dltQuery = "delete from {} where {}={}"
                pkColumnName = self._getPrimaryKeyColumn(data['table_name'])
                delete = self.syncDB.executeCommit(dltQuery.format(
                    data['table_name'], pkColumnName, data['row_id']))

                if(delete):
                    print('done')
                    self.setAsProcessed(data['inbox_id'])
                else:
                    self.setPriority(data['inbox_id'], 'tb_sync_inbox', 3)
                    print('error: {}'.format(
                        self.syncDB.getLastCommitError()['msg']))

    def processAck(self, data):

        obox = self.syncDB.executeFetchOne(
            f"select * from tb_sync_outbox where outbox_id = {data['query']}")

        if (outbox['data']['msg_type'] == 'INS'):
            status = 'need_pk_update'
        else:
            status = 'arrived'

        ack = self.outbox.update(data={
            'status': status
        }, where_clause={
            'outbox_id': data['query']
        })
        # ackQuery = "update tb_sync_outbox set is_arrived=1, status='arrived' where outbox_id = {}".format(
        #     data['query'])
        # ack = self.syncDB.executeCommit(ackQuery)
        if(not ack):
            self.setPriority(data['inbox_id'], 'tb_sync_inbox', 3)
            self.outbox.update(data={'status': 'error'}, where_clause={
                               'outbox_id': data['msg_id']})
            # errorQuery = 'update tb_sync_outbox set is_error=1 where outbox_id = {}'.format(
            #     data['msg_id'])
            # self.syncDB.executeCommit(errorQuery)

            self.systemlog.insert("processACK", "Gagal update ACK ID#{} ERROR: {}".format(
                data['inbox_id'], self.syncDB.getLastCommitError()['msg']))
        else:
            self.setAsProcessed(data['inbox_id'])
        return True

    def processReg(self, data):
        if (env.MASTER_MODE):
            time.sleep(0.2)
            regData = data['query'].split('#')
            reg = {}
            for item in regData:
                attributes = item.split(':')
                reg[attributes[0]] = attributes[1]

            # cek apakah ip address sudah terdaftar
            checkQuery = f"select count(*) as total from tb_sync_client where client_ip = '{reg['ip_address']}'"
            check = self.syncDB.executeFetchOne(checkQuery)
            if (check['data']['total'] > 0):
                outbox = {
                    'row_id': 0,
                    'table_name': '',
                    'msg_type': 'REG',
                    'msg_id': 0,
                    'query': f"status:ERROR#reason:IP Address sudah digunakan#for:{data['msg_id']}",
                    'client_unique_id': 0,
                    'client_ip': reg['ip_address'],
                    'client_port': reg['port'],
                    'client_key': reg['secret_key'],
                    'client_iv': reg['iv_key']
                }
                self.outbox.insert(outbox)
                self.setAsProcessed(data['inbox_id'])
            else:
                client_id_check_q = "select ifnull(max(client_unique_id), 0) as id from tb_sync_client"
                client_id = self.syncDB.executeFetchOne(client_id_check_q)
                if (client_id['data']['id'] == 0):
                    client_id = self.clientIdStartFrom
                else:
                    client_id = client_id['data']['id'] + 1
                sql = f"insert into tb_sync_client(client_unique_id, client_key, client_iv, client_port, client_ip) values({client_id}, '{reg['secret_key']}', '{reg['iv_key']}', {reg['port']}, '{reg['ip_address']}')"

                inserted = self.syncDB.executeCommit(sql)
                if (not inserted):
                    self.setPriority(data['inbox_id'], 'tb_sync_inbox', 3)
                else:
                    outbox = {
                        'row_id': 0,
                        'table_name': '',
                        'msg_type': 'REG',
                        'msg_id': 0,
                        'query': f"status:OK#id:{client_id}#for:{data['msg_id']}",
                        'client_unique_id': client_id
                    }
                    self.outbox.insert(outbox)
                    self.setAsProcessed(data['inbox_id'])
                    print("OK")
        else:
            outbox = {
                'row_id': 0,
                'table_name': '',
                'msg_type': 'REG',
                'msg_id': 0,
                'query': f"status:ERROR#reason:Host bukan master#for:{data['msg_id']}",
                'client_unique_id': 0,
                'client_ip': reg['ip_address'],
                'client_port': reg['port'],
                'client_key': reg['secret_key'],
                'client_iv': reg['iv_key']
            }
            self.outbox.insert(outbox)
            self.setAsProcessed(data['inbox_id'])
            print('OK')

    def getData(self):
        self.syncDB.connect()
        sql = "select * from tb_sync_inbox where status = 'waiting'"
        if (self.limitRow > 0):
            sql += f' {self.limitRow}'
        data = self.syncDB.executeFetchAll(sql, False)
        self.syncDB.close()
        return data

    def setAsProcessed(self, id, status='done'):
        set = self.inbox.update(
            data={'status': status}, where_clause={'inbox_id': id})
        # query = 'update tb_sync_inbox set is_process=1 where inbox_id = {}'.format(
        #     id)
        # print(set)


sync = Sync()
# sync.setPriority(2677, 'tb_sync_outbox', 2)
# sync.db.insError("test")
# sys.exit()
while True:
    inbox = sync.getData()
    if(inbox['execute_status']):
        if(inbox['data']):
            for item in inbox['data']:
                print(
                    "[{}] -> #{}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), item['msg_id']), end=" ")
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
                elif (msgType == 'REG'):
                    sync.processReg(item)
                else:
                    sync.syncDB.insError("Msg type not found for id=" +
                                         str(item['inbox_id']))
        else:
            time.sleep(1)
    else:
        print('Error')
        sys.exit()
    # sys.exit()
