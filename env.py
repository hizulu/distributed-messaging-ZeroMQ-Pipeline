MASTER_NODE = True
TEST_MASTER_MODE = True

# database
DB_HOST = "localhost"
DB_UNAME = "root"
DB_PASSWORD = ""
DB_PORT = 3306
DB_NAME = "db_ta"

UNIQUE_ID = 234
SINK_ADDR = 'tcp://192.168.229.1:5558'
RECEIVER_ADDR = 'tcp://192.168.229.1:5560'
# sink
SECRET_KEY = "sice2lrit9q2wvzx"
IV_KEY = "6YM6LfUkMAx6A27U"

# log
LOG_ROW_LIMIT = 10

# ventilator
VEN_MAX_ROW_PER_WORKER = 50
VEN_WORKER_ADDR = "tcp://*:5557"

# sync service
LIMIT_PROC_ROW = 100
THREAD_LIMIT = 4
