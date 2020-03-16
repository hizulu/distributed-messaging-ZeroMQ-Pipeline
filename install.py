from instalation import Instalation
from DatabaseConnection import DatabaseConnection
import sys
import re
import os
import json
import zmq
from encryption import AES256
import time

defaultSinkPort = 5558
defaultWorkerPort = 5557
defaultlogRowLimit = 0
defaultProcRow = 0
threadLimit = 4

print("Install Syncronization Service")
isMaster = input("[?] Apakah host ini adalah master? (y atau n): ")
isMaster = isMaster.lower()
if (isMaster != 'y' and isMaster != 'n'):
    print("[!] Input tidak sesuai. Masukkan `y` atau `n`")
    sys.exit()

isMaster = True if isMaster == 'y' else False


# if (not isMaster):
#     while True:
#         mode = int(input("[?] Pilih Mode(1 atau 2 Arah)? tulis angka saja: "))
#         if (mode > 2 or mode < 1):
#             print("[!] Input tidak sesuai. Masukkan `1` atau `2`")
#         else:
#             print(f"[/] Menggunakan Mode {mode} Arah")
#             break
mode = 2

# db config
while True:
    dbHost = input("[?] Masukkan Host DB: ")
    dbName = input("[?] Masukkan Nama DB: ")
    dbUser = input("[?] Masukkan Username DB: ")
    dbPass = input("[?] Masukkan Password DB: ")
    print("[/] Testing koneksi DB", end="...")
    db = DatabaseConnection(dbHost, dbUser, dbPass, dbName)
    try:
        db.connect()
    except Exception as e:
        print("ERROR:", e.args[1])
        continue
    print("OK")
    break

# cek table
if(isMaster):
    cekTableQuery = "show tables"
    tables = db.executeFetchAll(cekTableQuery)
    if (len(tables['data']) <= 0):
        print(
            '[!] Tidak ada tabel, tidak dapat melanjutkan proses. Isi tabel lalu ulangi lagi.')
        sys.exit()
#

ipaddr = input(
    "[?] Masukkan IP Address host yang dapat hubungi oleh host lain: ")
ip_candidates = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", ipaddr)
if (len(ip_candidates) <= 0):
    print('[!] IP Address tidak valid')
    sys.exit()
ipaddr = ip_candidates[0]
print(f"[/] Menggunakan `{ipaddr}` sebagai IP Address")

ins = Instalation(dbHost, dbName, dbUser, dbPass)
secretKey = ins.randomString()
ivKey = ins.randomString()

if (isMaster):
    ins.dropAllTrigger()
    ins.createSyncTable()
    ins.generateDefaultTrigger()
    unique_id = 1
    ins.setUniqueId(unique_id)

    ins.addUnixTimestampColumnToEveryTable()
    ins.generateSyncTrigger()
else:
    # menghapus isi dari setiap tabel dengan prefix
    # tb_sync
    print('[/] Menghapus data tabel sinkron')
    sync_tables = ['tb_sync_inbox', 'tb_sync_client',
                   'tb_sync_outbox', 'tb_sync_changelog']
    for table in sync_tables:
        print(f'[/] Menghapus data tabel `{table}`', end="...")
        sql = f"DELETE FROM {table}"
        deleted = db.executeCommit(sql)
        if(not deleted):
            print(db.getLastCommitError())
        print('OK') if deleted else print("ERROR")
    #

    while True:
        masterip = input('[?] Masukkan IP Address Master: ')
        ip_candidates = re.findall(
            r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", masterip)
        if (len(ip_candidates) <= 0):
            print('[!] IP Address tidak valid')
            continue
        masterip = ip_candidates[0]
        print(f"[/] Menggunakan `{masterip}` sebagai IP Address Master")
        break

    while True:
        masterSecretKey = input('[?] Masukkan Secret Key Master: ')
        if (len(masterSecretKey) < 16 or len(masterSecretKey) > 16):
            print(
                f"[!] Secret key harus 16 digit. Panjang karakter yang anda masukkan {len(masterSecretKey)}")
        else:
            break

    while True:
        masterIvKey = input('[?] Masukkan IV Key Master: ')
        if (len(masterIvKey) < 16 or len(masterIvKey) > 16):
            print(
                f"[!] Secret key harus 16 digit. Panjang karakter yang anda masukkan {len(masterIvKey)}")
        else:
            break

    print("[/] Registrasi client ke Master")
    regData = f"secret_key:{secretKey}#iv_key:{ivKey}#ip_address:{ipaddr}#port:5558"
    # mengirim menggunakan worker
    context = zmq.Context()
    sender = context.socket(zmq.PUSH)
    sender.connect(f"tcp://{masterip}:5558")
    enc = AES256()
    msg_id = int(time.time())
    jsonPacket = {
        'query': regData,
        'client_unique_id': 0,
        'timestamp': "",
        'sync_token': 0,
        'row_id': 0,
        'table_name': 'REG',
        'msg_id': msg_id,
        'msg_type': "REG",
        'master_status': 0
    },
    data = enc.encrypt(json.dumps(jsonPacket), masterSecretKey, masterIvKey)
    # data = jsonPacket
    encryptedPacket = {
        'sender_id': 0,
        'data': data
    }
    receiver = context.socket(zmq.PULL)
    receiver.bind(f"tcp://{ipaddr}:{defaultSinkPort}")
    print("[/] Mengirim data ke master...OK")
    sender.send_json(encryptedPacket)

    # print("[/] Menunggu balasan master")

    while True:
        print(".", end="")
        msg = receiver.recv_json()
        enc = AES256()
        try:
            plain = json.loads(enc.decrypt(ivKey, msg['data'], secretKey))
        except json.decoder.JSONDecodeError as e:
            continue
        msg['data'] = plain[0]
        data = msg['data']
        # print(data)
        if (data['msg_type'] == 'REG'):
            regData = data['query'].split('#')
            reg = {}
            for item in regData:
                attributes = item.split(':')
                reg[attributes[0]] = attributes[1]
            # print(reg)
            # print(f"{msg_id} x {reg['for']}")
            if (int(reg['for']) != msg_id):
                continue
            else:
                if (reg['status'] == 'OK'):
                    print("OK")
                    unique_id = reg['id']

                    if (mode == 2):
                        # memasukkan master ke tabel client
                        print("[/] Memasukkan master ke tabel client", end="...")
                        sql = f"""
                            insert into tb_sync_client(client_unique_id, client_key, client_iv, client_ip, client_port)
                            values(1, '{masterSecretKey}', '{masterIvKey}', '{masterip}', 5558)
                        """
                        inserted = db.executeCommit(sql)
                        print("OK") if inserted else print("ERROR")
                        #

                    # initializing
                    ins.setUniqueId(unique_id)
                    ins.dropAllTrigger()
                    ins.generateDefaultTrigger()
                    ins.generateSyncTrigger()
                    #

                    # send ACK
                    jsonPacket = {
                        'query': data['msg_id'],
                        'client_unique_id': 1,
                        'row_id': 0,
                        'table_name': 'REG',
                        'msg_id': 0,
                        'msg_type': "ACK",
                    },
                    data = enc.encrypt(json.dumps(jsonPacket),
                                       masterSecretKey, masterIvKey)
                    # data = jsonPacket
                    encryptedPacket = {
                        'sender_id': unique_id,
                        'data': data
                    }
                    sender.send_json(encryptedPacket)
                    break
                else:
                    print(f"ERROR: {reg['reason']}")
                    sys.exit()
# cetak env
env_file = open('env.py', 'w')
env_file.write(f"MASTER_MODE={isMaster}\n")
env_file.write(f"DB_HOST='{dbHost}'\n")
env_file.write(f"DB_UNAME='{dbUser}'\n")
env_file.write(f"DB_PASSWORD='{dbPass}'\n")
env_file.write(f"DB_PORT={3306}\n")
env_file.write(f"DB_NAME='{dbName}'\n")
env_file.write(f"UNIQUE_ID={unique_id}\n")
env_file.write(f"SINK_ADDR='tcp://{ipaddr}:{defaultSinkPort}'\n")
env_file.write(f"SECRET_KEY='{secretKey}'\n")
env_file.write(f"IV_KEY='{ivKey}'\n")
env_file.write(f"LOG_ROW_LIMIT={defaultlogRowLimit}\n")
env_file.write(f"VEN_WORKER_ADDR='tcp://*:{defaultWorkerPort}'\n")
env_file.write(f"LIMIT_PROC_ROW={defaultProcRow}\n")
env_file.write(f"THREAD_LIMIT={threadLimit}\n")
#
