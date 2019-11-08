from DatabaseConnection import DatabaseConnection

host = 'localhost'
username = 'rama'
password = 'ramapradana24'
database = 'db_ta'
rowLimit = '200'
db = DatabaseConnection(host, username,
                        password, database)

for i in range(1000):
    sql = """
    INSERT INTO tb_buku(`nama_buku`, `jenisbuku_id`, isbn)
    VALUES('buku', 1, 12341234)"""
    db.executeCommit(sql)
    print("{}".format(i+1))
