from DatabaseConnection import DatabaseConnection
import env
import sys
import time

db = DatabaseConnection(
    env.DB_HOST, env.DB_UNAME, env.DB_PASSWORD, env.DB_NAME)


option = sys.argv[1]
count = int(sys.argv[2])
delay = int(sys.argv[3])

if (delay > 0):
    for i in range(delay):
        print(delay)
        time.sleep(1)
        delay -= 1

table_name = 'tb_mahasiswa'
if (option == 'ins'):
    print(f"Testing INSERT {count} data")
    for i in range(count):
        print(f"Insert data-{i+1}...", end="...")
        insert = db.executeCommit(
            f'insert into {table_name}(nama) values("data-{i+1} from {env.UNIQUE_ID}")')
        print("OK") if insert else print("ERROR")
elif (option == 'upd'):
    data = db.executeFetchAll(f"select id from {table_name} limit {count}")
    # print(data)
    for item in data['data']:
        print(f"Updata data id ke {item['id']}", end="...")
        update = db.executeCommit(
            f"update {table_name} set nama='{time.time()}' where id={item['id']}")
        print("OK") if update else print("ERROR")
        if (not update):
            print(db.getLastCommitError())
            break

elif (option == 'del'):
    data = db.executeFetchAll(f"select id from {table_name} limit {count}")
    for item in data['data']:
        print(f"delete data id ke {item['id']}", end="...")
        delete = db.executeCommit(
            f"delete from {table_name} where id={item['id']}")
        print("OK") if delete else print("ERROR")
