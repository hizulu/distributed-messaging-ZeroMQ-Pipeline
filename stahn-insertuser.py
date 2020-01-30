import pymysql.cursors
import string
import random
import sys
import bcrypt
from DatabaseConnection import DatabaseConnection

host = '157.230.37.25'
username = 'stahnsimak'
password = 'st4hnS1m4k'
database = 'db_stahnsimak'


sso = DatabaseConnection(host, 'stahnsso',
                         'st4hnSS0', 'db_stahnidentity')

sql = """
    select * from tb_users where pass is not null
"""

res = sso.executeFetchAll(sql)
count = 1
sso.connect()
for item in res:

    hashedPassword = bcrypt.hashpw(item['pass'].encode('utf-8'),
                                   bcrypt.gensalt())

    insertSql = """
        update tb_users set password='{}' where user_id = {}
    """

    # print(insertSql.format(item['mahasiswa_id'], item['nim'], hashedPassword.decode(),
    #                        item['nama'], item['nim'], 1, item['email'], item['prodi_id'], item['fakultas_id'], 165, 3, password))
    # sys.exit()
    isInserted = sso.executeCommit(insertSql.format(
        hashedPassword.decode(), item['user_id']))

    if(isInserted):
        print("{}) {} => Sukses".format(count, item['user_id']))
    else:
        print(sso.getLastCommitError())
        print('{}) {} => Error'.format(count, item['user_id']))

    count += 1

sso.close()
