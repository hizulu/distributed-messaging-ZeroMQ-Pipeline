from DatabaseConnection import DatabaseConnection
import env
host = 'localhost'
username = 'rama'
password = 'ramapradana24'
database = 'db_ta'
rowLimit = '200'
db = DatabaseConnection(env.DB_HOST, env.DB_UNAME,
                        env.DB_PASSWORD, env.DB_NAME)

for i in range(100):
    nama_buku = "H1-{}".format(i+1)
    sql = "insert into tb_coba(nama) values('rama')"
    db.executeCommit(sql=sql)
    print("{}".format(i+1))
