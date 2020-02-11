from DatabaseConnection import DatabaseConnection
import env
host = 'localhost'
username = 'rama'
password = 'ramapradana24'
database = 'db_ta'
rowLimit = '200'
db = DatabaseConnection(env.DB_HOST, env.DB_UNAME,
                        env.DB_PASSWORD, env.DB_NAME)

for i in range(9):
    nama_buku = "Hello-{}".format(i+1)
    sql = """
    INSERT INTO tb_buku(`nama_buku`, `jenisbuku_id`, isbn)
    VALUES('{}', 1, 12341234)""".format(nama_buku)
    db.executeCommit(sql=sql)
    print("{}".format(i+1))
