import zmq
import env
from DatabaseConnection import DatabaseConnection

context = zmq.Context()
recv = context.socket(zmq.PULL)
recv.bind(env.RECEIVER_ADDR)
db = DatabaseConnection(env.DB_HOST, env.DB_UNAME,
                        env.DB_PASSWORD, env.DB_NAME)
sql = "update tb_outbox set is_arrived=1 where outbox_id = {}"
while True:
    msg = recv.recv_json()
    print(db.executeCommit(sql.format(msg['msg_id'])))
