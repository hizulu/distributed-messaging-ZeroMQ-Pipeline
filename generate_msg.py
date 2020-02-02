from DatabaseConnection import DatabaseConnection
import env
host = 'localhost'
username = 'rama'
password = 'ramapradana24'
database = 'db_ta'
rowLimit = '200'
db = DatabaseConnection(env.DB_HOST, env.DB_UNAME,
                        env.DB_PASSWORD, env.DB_NAME)

for i in range(10):
    sql = """
    INSERT INTO tb_buku(`nama_buku`, `jenisbuku_id`, isbn)
    VALUES('buku', 1, 12341234)"""
    db.executeCommit(sql=sql)
    print("{}".format(i+1))
