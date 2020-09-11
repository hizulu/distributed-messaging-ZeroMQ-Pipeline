MASTER_NODE = True
# database
DB_HOST = "localhost"
DB_UNAME = "rama"
DB_PASSWORD = "ramapradana24"
DB_PORT = 3306
DB_NAME = "db_autotrigger"

UNIQUE_ID = 234
SINK_ADDR = 'tcp://192.168.193.1:5558'
# sink
SECRET_KEY = "sice2lrit9q2wvzx"
IV_KEY = "6YM6LfUkMAx6A27U"

# log
LOG_ROW_LIMIT = 2

# ventilator
VEN_MAX_ROW_PER_WORKER = 50
VEN_WORKER_ADDR = "tcp://*:5557"

# sync service
LIMIT_PROC_ROW = 100
THREAD_LIMIT = 4
