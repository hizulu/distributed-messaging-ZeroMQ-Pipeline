# database
DB_HOST = "localhost"
DB_UNAME = "rama"
DB_PASSWORD = "ramapradana24"
DB_PORT = 3306
DB_NAME = "db_ta_monitor"
DB_SNC_NAME = 'db_ta1'

UNIQUE_ID = 234
SINK_ADDR = 'tcp://127.0.0.1:5558'
RECEIVER_ADDR = 'tcp://127.0.0.1:5560'

# sink
SECRET_KEY = "sice2lrit9q2wvzx"
IV_KEY = "6YM6LfUkMAx6A27U"

# log
LOG_ROW_LIMIT = '10'

# ventilator
VEN_MAX_ROW_PER_WORKER = 50
VEN_WORKER_ADDR = "tcp://*:5557"
