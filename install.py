from instalation import Instalation
from DatabaseConnection import DatabaseConnection
import sys
import re
import os
import json
import zmq
from encryption import AES256


print("Install Syncronization Service")
isMaster = input("[?] Apakah host ini adalah master? (y atau n): ")
isMaster = isMaster.lower()
if (isMaster != 'y' and isMaster != 'n'):
    print("[!] Input tidak sesuai. Masukkan `y` atau `n`")
    sys.exit()

isMaster = True if isMaster == 'y' else False

# db config
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
    sys.exit()
print("OK")

# cek table
if(isMaster):
    cekTableQuery = "show tables"
    tables = db.executeFetchAll(cekTableQuery)
    if (len(tables['data']) <= 0):
        print(
            '[!] Tidak ada tabel, tidak dapat melanjutkan proses. Isi tabel lalu ulangi lagi.')
        sys.exit()
#

ins = Instalation(db)
ins.dropAllTrigger()
ins.createSyncTable()
ins.generateDefaultTrigger()

ipaddr = input(
    "[?] Masukkan IP Address host yang dapat hubungi oleh host lain: ")
ip_candidates = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", ipaddr)
if (len(ip_candidates) <= 0):
    print('[!] IP Address tidak valid')
    sys.exit()
ipaddr = ip_candidates[0]
print(f"[/] Menggunakan `{ipaddr}` sebagai IP Address")

defaultSinkPort = 5558
defaultWorkerPort = 5557
defaultlogRowLimit = 0
defaultProcRow = 0
threadLimit = 4
secretKey = ins.randomString()
ivKey = ins.randomString()

if (isMaster):
    unique_id = 1
    ins.setUniqueId(unique_id)

    ins.addUnixTimestampColumnToEveryTable()
    ins.generateSyncTrigger()
else:
    masterip = input('[?] Masukkan IP Address Master: ')
    ip_candidates = re.findall(
        r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", masterip)
    if (len(ip_candidates) <= 0):
        print('[!] IP Address tidak valid')
        sys.exit()
    masterip = ip_candidates[0]
    print(f"[/] Menggunakan `{masterip}` sebagai IP Address Master")

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

    # memasukkan master ke tabel client
    print("[/] Memasukkan master ke tabel client", end="...")
    sql = f"""
        insert into tb_sync_client(client_unique_id, client_key, client_iv, client_ip, client_port)
        values(1, '{masterSecretKey}', '{masterIvKey}', '{masterip}', 5558)
    """
    inserted = db.executeCommit(sql)
    print("OK") if inserted else print("ERROR")

    print("[/] Registrasi client ke Master", end="...")
    regData = {
        'secret_key': secretKey,
        'iv_key': ivKey,
        'ip_address': ipaddr,
        'port': 5558
    }
    # mengirim menggunakan worker
    context = zmq.Context()
    sender = context.socket(zmq.PUSH)
    sender.connect(f"tcp://{masterip}:5558")
    enc = AES256()
    jsonPacket = {
        'query': json.dumps(regData),
        'client_unique_id': 0,
        'timestamp': "",
        'occur_at': 0,
        'sync_token': 0,
        'first_time_occur_at': 0,
        'row_id': 0,
        'table_name': '',
        'msg_id': 0,
        'msg_type': "REG",
        'master_status': 0
    },
    data = enc.encrypt(json.dumps(jsonPacket), masterSecretKey, masterIvKey)
    # data = jsonPacket
    print(data)
    encryptedPacket = {
        'sender_id': 0,
        'data': data
    }
    sender.send_json(encryptedPacket)


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
env_file.write(f"SECRET_KEY='{ivKey}'\n")
env_file.write(f"LOG_ROW_LIMIT={defaultlogRowLimit}\n")
env_file.write(f"VEN_WORKER_ADDR='tcp://*:{defaultWorkerPort}'\n")
env_file.write(f"LIMIT_PROC_ROW={defaultProcRow}\n")
env_file.write(f"THREAD_LIMIT={threadLimit}\n")
#
