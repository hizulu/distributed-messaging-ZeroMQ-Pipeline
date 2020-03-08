from DatabaseConnection import DatabaseConnection
import sys

host = '172.104.45.98'
username = 'laksita'
password = 'bgx2NyA3vFZgZnTU'
database = 'db_simak'
rowLimit = '200'

db = DatabaseConnection(host, username,
                        password, database)

tahun = 2019
semester = 1
tahunajaran = f"{tahun}{semester}"
kelasStartFrom = 65

prodiQuery = "select prodi_id, nama_prodi from tb_prodi where flag = 1"
prodi = db.executeFetchAll(prodiQuery)

for p in prodi['data']:
    # mengambil mktawar
    mktawarQuery = f"""
        select mktawar_id, matakuliah_id, kelas, program_id, prodi_id  from tb_mktawar where tahunajaran={tahun} and semester={semester}
        and prodi_id = 3 and tb_mktawar.flag=1 order by matakuliah_id, program_id, prodi_id
    """

    mktawar = db.executeFetchAll(mktawarQuery)
    for mk in mktawar['data']:
        print(
            f"{mk['matakuliah_id']}#{mk['prodi_id']}#{mk['program_id']}#{mk['kelas']}")
    sys.exit()
