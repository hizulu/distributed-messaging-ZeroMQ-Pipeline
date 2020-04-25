from DatabaseConnection import DatabaseConnection
import env as env
import sys
from outbox import Outbox
from systemlog import SystemLog
from inbox import Inbox
import json
import time
import datetime
import threading
import os
from ast import literal_eval


class Sync:

    def __init__(self):
        self.syncDB = DatabaseConnection(
            env.DB_HOST, env.DB_UNAME, env.DB_PASSWORD, env.DB_NAME)
        # self.statusDB = DatabaseConnection(
        #     env.DB_HOST, env.DB_UNAME, env.DB_PASSWORD, env.DB_NAME)
        self.limitRow = env.LIMIT_PROC_ROW
        self.outbox = Outbox(self.syncDB)
        self.systemlog = SystemLog()
        self.inbox = Inbox(self.syncDB)
        self.outbox = Outbox(self.syncDB)
        self.clientIdStartFrom = 10
        self.updateToZeroHistory = set([])
        self.PKFileName = 'pk'

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
        print(f"Inbox ID: {data['inbox_id']}")
        print(f"Type: {data['msg_type']}")
        # mengirim bahwa pesan sedang di proses
        # self.sendStatusUpdate(data, 'PROC')

        insert = self.syncDB.executeCommit(data['query'])
        rowId = self.syncDB.lastRowId

        if (insert):
            # hanya master yang mengirim NEEDPK ke slave
            # if(env.MASTER_MODE):
            #     self.sendStatusUpdate(data, 'NEEDPK')

            print("Status: OK")

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
                    'client_unique_id': data['client_unique_id'],
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

    def getZeroPKHistory(self):
        file = open(self.PKFileName, 'r')
        file_value = file.read()
        if (file_value):
            self.updateToZeroHistory = set(literal_eval(file_value))
        file.close()

    def updateZeroPKHistory(self):
        file = open(self.PKFileName, 'w')
        file.write(str(list(self.updateToZeroHistory)))
        file.close()
        # method ini digunakan untuk memproses update primary key
        # primary key yang digunakan adalah primary key dari master

    def processPrimaryKey(self, data):
        print(f"Inbox ID: {data['inbox_id']}")
        print(f"Type: {data['msg_type']}")

        if (data['row_id'] == int(data['query'])):
            self.setAsProcessed(data['inbox_id'])
            print("Status: OK Same PK")
            return True

        self.getZeroPKHistory()
        # check apakah pri ini ada di history update 0
        row_id = data['row_id']

        if (len(self.updateToZeroHistory) > 0):
            # mencari apakah ada history\
            code = f"{data['table_name']}{data['row_id']}"
            zeroExecMode = False

            if (code in self.updateToZeroHistory):
                print("Mode: 0 Exec")
                data['row_id'] = 0
                res = self.doUpdatePK(data)
                if (res):
                    self.updateToZeroHistory.remove(code)
            else:
                # skip
                res = self.doUpdatePK(data)
        else:
            # langsung eksekusi update
            res = self.doUpdatePK(data)

        print("Status: ", end="")
        print("OK") if res else print("ERROR")
        self.updateZeroPKHistory()
        # mencari nama kolom primary key
        # print(db_name)

    def doUpdatePK(self, data):
        db_name = env.DB_NAME
        sql = """
            select COLUMN_NAME from information_schema.COLUMNS
            where TABLE_SCHEMA='{}' and TABLE_NAME='{}'
            and COLUMN_KEY='PRI'
        """.format(db_name, data['table_name'])
        res = self.syncDB.executeFetchOne(sql)
        if (res['execute_status']):
            primary_key = res['data']['COLUMN_NAME']
            update_from = data['row_id']
            update_to = data['query']
            print(f"From: {update_from} To: {update_to}")
            sql = "update {} set {}={} where {}={}"
            update = self.syncDB.executeCommit(sql.format(
                data['table_name'], primary_key, update_to, primary_key, update_from))

            if (update):
                # set status outbox menjadi done
                if (data['msg_id'] == 0):
                    # pesan PRI di generate oleh slave
                    # mengambil pesan INS
                    insMsg = self.syncDB.executeFetchOne(
                        f"select * from tb_sync_inbox where row_id={data['query']} and msg_type='INS' and table_name='{data['table_name']}'")
                    self.sendStatusUpdate(insMsg['data'], 'DONE')
                else:
                    # pesan PRI yang diterima dari master
                    updateQ = f"update tb_sync_outbox set status='done' where table_name='{data['table_name']}' and msg_type='INS' and row_id = {data['row_id']}"
                    self.syncDB.executeCommit(updateQ)

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
                return True
            else:
                # update to zero history
                self.setPriority(data['inbox_id'],
                                 'tb_sync_inbox', data['priority'] + 1)
                allowToAdd = True
                for item in self.updateToZeroHistory:
                    if (data['table_name'] in item):
                        allowToAdd = False
                        break

                if (allowToAdd):
                    code = f"{data['table_name']}{data['row_id']}"
                    self.updateToZeroHistory.add(code)
                    update = self.syncDB.executeCommit(sql.format(
                        data['table_name'], primary_key, 0, primary_key, update_from))
                return False
                # ubah primary key goal menjadi 0

    def processUpdate(self, data):
        # self.sendStatusUpdate(data, "PROC")
        print(f"Inbox ID: {data['inbox_id']}")
        print(f"Type: {data['msg_type']}")
        # cek apakah pesan ini lebih baru dibantingkan data sekarnag
        primary_key = self._getPrimaryKeyColumn(data['table_name'])
        row_data = self.syncDB.executeFetchOne(
            f"select * from {data['table_name']} where {primary_key}={data['row_id']}")
        print(
            f"{row_data['data']['last_action_at']} : {data['first_time_occur_at']}")
        if (row_data['data']['last_action_at'] < data['first_time_occur_at']):
            # data yang di proses adalah data baru
            execute = self.syncDB.executeCommit(data['query'])
            if (not execute):
                print("Status: ERROR")
            else:
                self.setAsProcessed(data['inbox_id'])
                self.sendStatusUpdate(data, "DONE")
                print("Status: OK")
        else:
            # data yang di proses adlaah data lama
            self.setAsProcessed(data['inbox_id'])
            self.sendStatusUpdate(data, "DONE")
            print("Status: OLD DATA")

    def processDelete(self, data):
        # self.sendStatusUpdate(data, "PROC")
        # cek apakah ada inbox yang bertipe PRI
        # berdasarkan primari key yang masuk
        # jika ada mata update inbox tersebut jadi terproses
        # jika tidak ada lakukan delete seperti biasa
        print(f"Inbox ID: {data['inbox_id']}")
        print(f"Type: {data['msg_type']}")
        checkQuery = """
            select count(inbox_id) as total from tb_sync_inbox where msg_type = 'PRI'
            and status = 'waiting'
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
                    self.sendStatusUpdate(data, "DONE")
                    self.setAsProcessed(data['inbox_id'])
                    print("Status: OK")
                else:
                    self.setPriority(data['inbox_id'], 'tb_sync_inbox', 3)
                    print("Status: ERROR")

    def processAck(self, data):
        print(f"Inbox ID: {data['inbox_id']}")
        print(f"Type: {data['msg_type']}")
        obox = self.syncDB.executeFetchOne(
            f"select * from tb_sync_outbox where outbox_id = {data['query']}")
        ack = True
        if(obox['data']):
            if (obox['data']['msg_type'] == 'INS'):
                status = 'need_pk_update'
            else:
                status = 'arrived'

            ack = self.outbox.update(data={
                'status': status
            }, where_clause={
                'outbox_id': data['query']
            })
            # ack = self.syncDB.executeCommit(
            #     f"update tb_sync_outbox set status='{status}' where outbox_id={data['query']}")
        # ackQuery = "update tb_sync_outbox set is_arrived=1, status='arrived' where outbox_id = {}".format(
        #     data['query'])
        # ack = self.syncDB.executeCommit(ackQuery)
        if(not ack):
            self.outbox.update(data={'status': 'error'}, where_clause={
                               'outbox_id': data['msg_id']})
            print("Status: ERROR")
            # errorQuery = 'update tb_sync_outbox set is_error=1 where outbox_id = {}'.format(
            #     data['msg_id'])
            # self.syncDB.executeCommit(errorQuery)

            # self.systemlog.insert("processACK", "Gagal update ACK ID#{} ERROR: {}".format(
            #     data['inbox_id'], self.statusDB.getLastCommitError()['msg']))
        else:
            self.setAsProcessed(data['inbox_id'])
            print("Status: OK")

    def processReg(self, data):
        print(f"Inbox ID: {data['inbox_id']}")
        print(f"Type: {data['msg_type']}")
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
                    print("Status: OK")
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
            print(f'Status: ERROR')

    def getData(self):
        self.syncDB.connect()
        sql = "select * from tb_sync_inbox where status = 'waiting' order by priority asc, inbox_id asc, occur_at asc"
        if (self.limitRow > 0):
            sql += f' limit {self.limitRow}'
        data = self.syncDB.executeFetchAll(sql, False)
        self.syncDB.close()
        return data

    def getStatusInbox(self):
        sql = "select * from tb_sync_inbox where status = 'waiting' and (msg_type = 'ACK' or msg_type = 'DONE') order by priority asc, inbox_id asc, occur_at asc"
        if (self.limitRow > 0):
            sql += f' {self.limitRow}'
        data = self.syncDB.executeFetchAll(sql)
        return data

    def getSyncInbox(self):
        sql = "select * from tb_sync_inbox where status = 'waiting' and (msg_type = 'INS' or msg_type = 'UPD' or msg_type = 'DEL' or msg_type = 'REG' or msg_type = 'PRI') order by priority asc, inbox_id asc, occur_at asc"
        if (self.limitRow > 0):
            sql += f' {self.limitRow}'
        data = self.syncDB.executeFetchAll(sql)
        return data

    def setAsProcessed(self, id, status='done'):
        set = self.inbox.update(
            data={'status': status}, where_clause={'inbox_id': id})
        # query = 'update tb_sync_inbox set is_process=1 where inbox_id = {}'.format(
        #     id)
        # print(set)

    def sendStatusUpdate(self, data, status):
        return self.outbox.insert({
            'row_id': data['row_id'],  # local row id
            'table_name': data['table_name'],
            'msg_type': status,
            'query': data['msg_id'],  # receiver outbox_id
            'client_unique_id': data['client_unique_id'],
            'msg_id': 0,
            'priority': 1
        })

    def updateOutboxStatus(self, id, status, inbox_id):
        upd = self.syncDB.executeCommit(
            f"update tb_sync_outbox set status='{status}' where outbox_id={id}")
        if (upd):
            self.setAsProcessed(inbox_id)
        else:
            self.setPriority(inbox_id, 'tb_sync_inbox', 3)

    def canProcessMsg(self, data):
        watchedMsgType = ['INS', 'UPD', 'DEL']
        if (data['msg_type'] not in watchedMsgType):
            return True

        # cek apakah ada pesan watchedMsgType yang blm selesai
        # sebelum inbox_id ini

        # jika slave, harus memastika semua outbox nya selesai di proses di master
        # lalu eksekusi inbox
        if (not env.MASTER_MODE):
            previousMsgs = self.syncDB.executeFetchOne(
                "select count(*) as total from tb_sync_outbox where (msg_type = 'INS' or msg_type='UPD' or msg_type='DEL') and status <> 'done'")

            if (previousMsgs['data']['total'] > 0):
                return False
            else:
                return True

        print(previousMsgs)

    def process(self, inbox):
        if(inbox):
            for item in inbox:
                # proses pesan selain INS, UPD dan DEL terlebih dahulu
                # jgn proses pesan utama jika masih ada pesan INS UPD DEL yang belum selesai

                # jika proses adalah INS UPD DEL, lakukan pengecekan pesan tertunda
                delayMsgInboxQ = "select count(*) from tb_sync_inbox where status "
                print(
                    "[{}] -> #{}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), item['msg_id']), end=" ")
                msgType = item['msg_type']
                if(msgType == 'INS'):
                    self.processInsert(item)
                elif(msgType == 'UPD'):
                    self.processUpdate(item)
                elif(msgType == 'DEL'):
                    self.processDelete(item)
                elif(msgType == 'ACK'):
                    self.processAck(item)
                elif(msgType == "PRI"):
                    self.processPrimaryKey(item)
                elif (msgType == 'REG'):
                    self.processReg(item)
                elif (msgType == 'PROC'):
                    print(self.updateOutboxStatus(
                        item['query'], "processing", item['inbox_id']))
                elif (msgType == 'NEEDPK'):
                    print(self.updateOutboxStatus(
                        item['query'], "need_pk_update", item['inbox_id']))
                elif (msgType == 'DONE'):
                    done = self.statusDB.executeCommit(
                        f"update tb_sync_outbox set status = 'done' where outbox_id = {item['query']}")

                    if (done):
                        print(self.statusDB.executeCommit(
                            f"update tb_sync_inbox set status='done' where inbox_id={item['inbox_id']}"))
                    else:
                        print("False")
                    # print(self.updateOutboxStatus(
                    #     item['query'], "done", item['inbox_id']))
                else:
                    self.syncDB.insError("Msg type not found for id=" +
                                         str(item['inbox_id']))

                # print(f"finish at: {time.time()}")
                file = open("proctime.text", 'a')
                file.write(f"{time.time()}\n")
                file.close()

        else:
            time.sleep(0.3)


sync = Sync()
# sync.setPriority(2677, 'tb_sync_outbox', 2)
# sync.db.insError("test")
# sys.exit()

while True:
    inbox = sync.getData()
    if(inbox['execute_status']):
        if(inbox['data']):
            for item in inbox['data']:
                print('---------------------')
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
                elif (msgType == 'PROC'):
                    print(sync.updateOutboxStatus(
                        item['query'], "processing", item['inbox_id']))
                elif (msgType == 'NEEDPK'):
                    print(sync.updateOutboxStatus(
                        item['query'], "need_pk_update", item['inbox_id']))
                elif (msgType == 'DONE'):
                    print(f"Inbox_id: {item['inbox_id']}")
                    print(f"Type: {item['msg_type']}")
                    sync.updateOutboxStatus(
                        item['query'], "done", item['inbox_id'])
                    print("Status: OK")
                else:
                    sync.syncDB.insError("Msg type not found for id=" +
                                         str(item['inbox_id']))

                # print(f"finish at: {time.time()}")
                file = open("proctime.text", 'a')
                file.write(f"{time.time()}\n")
                file.close()

        else:
            time.sleep(0.2)
    else:
        print('Error')
        # sys.exit()
    # sys.exit()
