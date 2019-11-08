import pymysql.cursors
from DatabaseConnection import DatabaseConnection
import sys

host = '172.104.45.98'
username = 'laksita'
password = 'bgx2NyA3vFZgZnTU'
database = 'db_simak'
rowLimit = '200'

db = DatabaseConnection(host, username,
                        password, database)


sql = """
    SELECT tb_mahasiswa.mahasiswa_id, nim, nama, tb_mahasiswa.program_id FROM tb_mahasiswa 
    JOIN tb_krs ON tb_krs.mahasiswa_id = tb_mahasiswa.mahasiswa_id 
    JOIN tb_mktawar ON tb_krs.`mktawar_id` = tb_mktawar.`mktawar_id`
    WHERE tb_krs.`tahunajaran`=2019 AND tb_krs.semester=1 
    AND tb_mktawar.`program_id` <> tb_mahasiswa.program_id
    and tb_krs.flag = 1
    GROUP BY tb_mahasiswa.`mahasiswa_id`
"""
res = db.executeFetchAll(sql)
print("Memproses {} data".format(len(res)))
queryKrs = """
    Select krs_id, tb_krs.mktawar_id, program_id, tb_mktawar.matakuliah_id, kelas from tb_krs 
    join tb_mktawar on tb_mktawar.mktawar_id = tb_krs.mktawar_id
    where mahasiswa_id = {} and tb_krs.tahunajaran=2019 and tb_krs.semester=1 and tb_krs.flag=1"""
krs = None

queryPenawaranTerkait = """
    select mktawar_id, kelas, program_id, matakuliah_id from tb_mktawar where tahunajaran=2019 and 
    semester=1 and program_id = {} and matakuliah_id= {} 
    and kelas='{}' and flag=1
"""

queryUpdateKrs = "update tb_krs set mktawar_id = {} where krs_id = {}"

diproses = 0
for item in res:
    diproses += 1
    print(
        "memproses data ke-{}: {} - {} - {}".format(diproses, item['nim'], item['nama'], item['program_id']))
    krs = db.executeFetchAll(queryKrs.format(item['mahasiswa_id']))
    # print(krs)
    for mk in krs:
        mkTerkait = db.executeFetchAll(queryPenawaranTerkait.format(
            item['program_id'], mk['matakuliah_id'], mk['kelas']))
        db.executeCommit(queryUpdateKrs.format(
            mkTerkait[0]['mktawar_id'], mk['krs_id']))
        print(
            "~~ Update KRS {}: {} -> {}".format(mk['krs_id'], mk['mktawar_id'], mkTerkait[0]['mktawar_id']))

print("FINISH")
