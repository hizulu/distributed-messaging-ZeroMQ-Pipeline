from instalation import Instalation
from DatabaseConnection import DatabaseConnection
import sys


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
#
ipaddr = input(
    "[?] Masukkan IP Address host yang dapat hubungi oleh host lain: ")
