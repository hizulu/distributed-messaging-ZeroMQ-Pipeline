from log import Log
from ventilator import Ventilator
from encryption import AES256
import time
import json
import sys
import env

print(env.DB_HOST)
sys.exit()

log = Log()
ven = Ventilator()
task = log.getUnproceessLog()
startTime = int(round(time.time() * 1000))
ven.send(task)
print("start time : {}".format(startTime))
sys.exit()
